MODULES = {
    "azure_storage_account": {
        "description": "Azure Storage Account using the approved lab module.",
        "path": "ai-terraform-mcp-lab/modules/azure-storage-account",
        "required": ["name", "resource_group_name", "location", "environment", "account_replication_type"],
        "optional": {
            "account_tier": "Standard",
            "min_tls_version": "TLS1_2",
            "https_traffic_only_enabled": True,
            "tags": {},
        },
        "allowed": {
            "account_tier": ["Standard"],
            "account_replication_type": ["LRS", "GRS", "RAGRS", "ZRS"],
            "min_tls_version": ["TLS1_2"],
        },
    }
}

def list_modules():
    return [{"name": k, "description": v["description"], "path": v["path"]} for k, v in MODULES.items()]

def get_module(name):
    if name not in MODULES:
        raise ValueError(f"Unknown approved module: {name}")
    return MODULES[name]
