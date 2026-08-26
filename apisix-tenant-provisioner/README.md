PISIX Tenant Route Provisioner CLI

A lightweight, automated Python CLI tool designed to provision idempotent routes dynamically in Apache APISIX for new SaaS tenants orchestrated via Nomad and registered inside HashiCorp Consul.

## Key Features

- **Regex Slug Validation**: Automatically rejects malformed tenant slugs before interacting with any cluster infrastructure.
- **Idempotent Network Engine**: Uses deterministic endpoints via HTTP `PUT` requests (`/apisix/admin/routes/{tenant_slug}`) to safely execute updates without duplicate drift.
- **Consul Service Mesh Discovery Integration**: Maps the gateway incoming traffic rules dynamically onto dynamic infrastructure endpoints without static upstream host bindings.
- **Dry-Run Mode Execution**: Pre-flights configurations safely onto the standard screen output interface without touching real infrastructure states.
- **Durable Audit Trail Logging**: Continuously updates an external state record file (`tenant_routes.log`) outside of APISIX runtime storage.

## Pre-requisites

Make sure your machine runs Python 3.10+ and you are working inside an isolated workspace.

```bash
# Setup the project boundary space
python3 -m venv .venv
source .venv/bin/activate

# Fetch dependency binaries
pip install -r requirements.txt
```

## Running the Configuration

Adjust parameters inside the local `config.yaml` layout space to align targets:

```yaml
apisix:
  admin_api_url: "http://localhost:9180/apisix/admin"
  admin_key: "edd1c9f034335f136f87ad84b625c8f1"

tenant:
  base_domain: "yourcompany.com"
  slug_regex: "^[a-z0-9-]+$"

consul:
  service_name_prefix: "tenant-service-"
```

## Usage Syntax Examples

### 1. Execute Pre-flight Dry Run Plan
```bash
python provisioner.py --slug apple --dry-run
```

### 2. Execute Real Production Infrastructure Target Mapping
```bash
python provisioner.py --slug apple
```

