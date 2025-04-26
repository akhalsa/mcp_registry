#!/usr/bin/env python3
import os

import aws_cdk as cdk

from infrastructure.mcp_registry_stack import McpRegistryStack


app = cdk.App()

env_name = app.node.try_get_context("env")
if env_name is None:
    raise Exception("Context variable 'env' must be set (e.g., --context env=prod)")

# Accounts and regions
environments = {
    "prod": cdk.Environment(account="111122223333", region="us-east-1"),
    "dev":  cdk.Environment(account="444455556666", region="us-east-1"),
}

if env_name not in environments:
    raise Exception(f"Unknown environment: {env_name}")

McpRegistryStack(app, f"McpRegistryStack-{env_name}", env=environments[env_name])

app.synth()

