import argparse
import logging
import re
import requests
import yaml

# Setup structured logging to both a file and the console output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("tenant_routes.log"),
        logging.StreamHandler()
    ]
)

def load_config():
    """Loads operational configurations from the local yaml layout."""
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)

def validate_slug(slug, regex_pattern):
    """Validates the tenant slug format against the company standard regex."""
    if not re.match(regex_pattern, slug):
        return False
    return True

def create_apisix_route(config, tenant_slug, subdomain, consul_service):
    """
    Sends an idempotent HTTP PUT request to the APISIX Admin API 
    to map the tenant's subdomain directly onto its Consul service destination.
    """
    admin_url = config['apisix']['admin_api_url']
    admin_key = config['apisix']['admin_key']
    
    # Enforcing Idempotency: Using the unique tenant slug as the permanent Route ID
    route_endpoint = f"{admin_url}/routes/{tenant_slug}"
    
    headers = {
        "X-API-KEY": admin_key,
        "Content-Type": "application/json"
    }
    
    # Payload configured to route traffic dynamically using Consul Service Discovery
    payload = {
        "uri": "/*",               # Catch all routes for this tenant subdomain
        "hosts": [subdomain],      # Match the custom tenant domain
        "upstream": {
            "type": "roundrobin",  
            "discovery_type": "consul", 
            "service_name": consul_service 
        }
    }
    
    try:
        # PUT method ensures that repeating the execution overwrites/updates safely without duplicates
        response = requests.put(route_endpoint, headers=headers, json=payload, timeout=10)
        
        # Fixed Line: Validates successful HTTP 200 (OK) or HTTP 201 (Created) status codes
        if response.status_code in [200, 201]:
            logging.info(f"Successfully provisioned APISIX route for tenant '{tenant_slug}' (HTTP {response.status_code})")
            return True
        else:
            logging.error(f"Failed to create route in APISIX. Status: {response.status_code}, Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        logging.error(f"Network connection error while reaching APISIX Admin API: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Automate APISIX Route Creation for SaaS Tenants")
    parser.add_argument("--slug", required=True, help="The unique tenant slug designation (e.g., apple)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate execution pathways without committing API changes")
    
    args = parser.parse_args()
    config = load_config()
    
    tenant_slug = args.slug
    dry_run_mode = args.dry_run
    
    # Step 1: Input Validation
    regex_rule = config['tenant']['slug_regex']
    if not validate_slug(tenant_slug, regex_rule):
        logging.error(f"Invalid tenant slug: '{tenant_slug}'. Configuration standard requires format: {regex_rule}")
        return

    # Step 2: Build Naming Formats
    subdomain = f"{tenant_slug}.{config['tenant']['base_domain']}"
    consul_service = f"{config['consul']['service_name_prefix']}{tenant_slug}"
    
    logging.info(f"Initiating dynamic routing process for tenant: '{tenant_slug}'")

    # Step 3: Handle Dry Run Simulation Guard
    if dry_run_mode:
        logging.info(f"[DRY-RUN] Target Subdomain Matrix: {subdomain}")
        logging.info(f"[DRY-RUN] Dynamic Upstream Profile: Consul Service Discovery Mode")
        logging.info(f"[DRY-RUN] Registered Service Query Key: '{consul_service}'")
        logging.info(f"[DRY-RUN] Target API Gateway Route Hook: {config['apisix']['admin_api_url']}/routes/{tenant_slug}")
        logging.info(f"[DRY-RUN] Simulation path complete. No modifications committed to the live environment.")
        return

    # Step 4: Live Cluster Execution
    create_apisix_route(config, tenant_slug, subdomain, consul_service)

if __name__ == "__main__":
    main()