#!/usr/bin/env python3
import aws_cdk as cdk
import os
from dotenv import load_dotenv

from infrastructure.mcp_registry_stack import McpRegistryStack

# Load environment variables from .env file
load_dotenv()

app = cdk.App()

# Read which environment to deploy (prod/dev)
env_name = app.node.try_get_context("env")
if env_name is None:
    raise Exception("Context variable 'env' must be set (e.g., --context env=prod)")

# Define environment settings from environment variables
environments = {
    "prod": cdk.Environment(
        account=os.environ.get("CDK_PROD_ACCOUNT", "000000000000"),
        region=os.environ.get("CDK_PROD_REGION", "us-east-1"),
    ),
    "dev": cdk.Environment(
        account=os.environ.get("CDK_DEV_ACCOUNT", "000000000000"),
        region=os.environ.get("CDK_DEV_REGION", "us-east-1"),
    ),
}

# Validate that the env_name is one we know
if env_name not in environments:
    raise Exception(f"Unknown environment: {env_name}")

# Create the stack
McpRegistryStack(app, f"McpRegistryStack-{env_name}", env=environments[env_name])

app.synth()
