import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from .catalog import get_module, list_modules
from .github_client import GitHubClient

mcp = FastMCP("terraform-ai-lab")
github = GitHubClient()

@mcp.tool()
def list_approved_modules() -> str:
    """List Terraform modules allowed for generation."""
    return json.dumps(list_modules(), indent=2)

@mcp.tool()
def get_approved_module(module_name: str) -> str:
    """Return schema and rules for an approved Terraform module."""
    return json.dumps(get_module(module_name), indent=2)

@mcp.tool()
def validate_request(module_name: str, values_json: str) -> str:
    """Validate values against the approved module."""
    module = get_module(module_name)
    values = json.loads(values_json)
    errors = []
    for key in module["required"]:
        if key not in values or values[key] in (None, ""):
            errors.append(f"Missing required value: {key}")
    for key, allowed in module.get("allowed", {}).items():
        if key in values and values[key] not in allowed:
            errors.append(f"{key} must be one of: {', '.join(allowed)}")
    if "name" in values and not re.fullmatch(r"[a-z0-9-]{3,24}", values["name"]):
        errors.append("name must contain only lowercase letters, numbers and hyphens, 3-24 chars")
    if "environment" in values and values["environment"] not in ["dev", "qa", "prod"]:
        errors.append("environment must be dev, qa or prod")
    return json.dumps({"valid": not errors, "errors": errors}, indent=2)

@mcp.tool()
def generate_storage_account(values_json: str) -> str:
    """Generate Terraform root configuration from the approved Storage Account module."""
    values = json.loads(values_json)
    validation = json.loads(validate_request("azure_storage_account", values_json))
    if not validation["valid"]:
        raise ValueError(json.dumps(validation))
    tags = dict(values.get("tags", {}))
    tags.setdefault("environment", values["environment"])

    main = '''terraform {
  required_version = ">= 1.6.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}
provider "azurerm" {
  features {}
}
module "storage_account" {
  source = "../../modules/azure-storage-account"
  name                       = var.name
  resource_group_name        = var.resource_group_name
  location                   = var.location
  environment                = var.environment
  account_replication_type   = var.account_replication_type
  account_tier               = var.account_tier
  min_tls_version            = var.min_tls_version
  https_traffic_only_enabled = var.https_traffic_only_enabled
  tags                       = var.tags
}
'''
    variables = '''variable "name" { type = string }
variable "resource_group_name" { type = string }
variable "location" { type = string }
variable "environment" { type = string }
variable "account_replication_type" { type = string }
variable "account_tier" { type = string }
variable "min_tls_version" { type = string }
variable "https_traffic_only_enabled" { type = bool }
variable "tags" { type = map(string) }
'''
    tfvars = {
        "name": values["name"],
        "resource_group_name": values["resource_group_name"],
        "location": values["location"],
        "environment": values["environment"],
        "account_replication_type": values["account_replication_type"],
        "account_tier": values.get("account_tier", "Standard"),
        "min_tls_version": values.get("min_tls_version", "TLS1_2"),
        "https_traffic_only_enabled": values.get("https_traffic_only_enabled", True),
        "tags": tags,
    }
    lines = []
    for key, value in tfvars.items():
        if isinstance(value, bool):
            rendered = str(value).lower()
        elif isinstance(value, dict):
            rendered = json.dumps(value, indent=2)
        else:
            rendered = json.dumps(value)
        lines.append(f"{key} = {rendered}")
    return json.dumps({
        "directory": f"{os.environ['GITHUB_GENERATED_ROOT']}/{values['environment']}/storage-{values['name']}",
        "files": {"main.tf": main, "variables.tf": variables, "terraform.tfvars": "\n".join(lines) + "\n"},
    }, indent=2)

@mcp.tool()
def create_branch(branch_name: str) -> str:
    """Create a feature branch from the configured base branch."""
    base = os.environ.get("GITHUB_BASE_BRANCH", "master")
    github.create_branch(branch_name, base)
    return f"Created branch {branch_name} from {base}"

@mcp.tool()
def write_generated_files(branch_name: str, directory: str, files_json: str) -> str:
    """Write generated Terraform files to a GitHub branch."""
    files = json.loads(files_json)
    commits = []
    for name, content in files.items():
        commits.append(github.upsert_file(f"{directory}/{name}", content, branch_name, f"feat(terraform): generate {name}"))
    return json.dumps({"branch": branch_name, "commits": commits}, indent=2)

@mcp.tool()
def terraform_validate(files_json: str) -> str:
    """Run terraform fmt, init and validate without apply."""
    files = json.loads(files_json)
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        for name, content in files.items():
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
        fmt = subprocess.run(["terraform", "fmt", "-check"], cwd=root, capture_output=True, text=True)
        if fmt.returncode:
            return json.dumps({"valid": False, "stage": "fmt", "output": fmt.stdout + fmt.stderr})
        init = subprocess.run(["terraform", "init", "-backend=false", "-input=false"], cwd=root, capture_output=True, text=True)
        if init.returncode:
            return json.dumps({"valid": False, "stage": "init", "output": init.stdout + init.stderr})
        validate = subprocess.run(["terraform", "validate"], cwd=root, capture_output=True, text=True)
        return json.dumps({"valid": validate.returncode == 0, "stage": "validate", "output": validate.stdout + validate.stderr}, indent=2)

@mcp.tool()
def create_draft_pr(branch_name: str, title: str, body: str) -> str:
    """Create a draft Pull Request to the configured base branch."""
    base = os.environ.get("GITHUB_BASE_BRANCH", "master")
    pr = github.create_pull_request(branch_name, base, title, body)
    return json.dumps({"number": pr["number"], "url": pr["html_url"], "draft": pr["draft"]}, indent=2)

if __name__ == "__main__":
    mcp.run(transport="stdio")
