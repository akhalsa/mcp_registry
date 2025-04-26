from aws_cdk import Stack
from aws_cdk import aws_s3 as s3
from constructs import Construct

class McpRegistryStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        mcp_registry_landing_zone = s3.Bucket(self, "MCP-Registry-Landing-Zone", versioned=True)