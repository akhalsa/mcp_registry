import aws_cdk as core
import aws_cdk.assertions as assertions

from mcp_registry.mcp_registry_stack import McpRegistryStack

# example tests. To run these tests, uncomment this file along with the example
# resource in mcp_registry/mcp_registry_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = McpRegistryStack(app, "mcp-registry")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
