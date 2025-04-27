from aws_cdk import (
    Stack,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_ec2 as ec2,
    aws_logs as logs,
    CfnOutput
)
from constructs import Construct

class ExamplesStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create a VPC (use 2 AZs for availability)
        vpc = ec2.Vpc(self, "ExampleServerVpc",
            max_azs=2,
            nat_gateways=0,  # No NAT Gateway
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                )
            ]
        )

        # Create ECS Cluster
        cluster = ecs.Cluster(self, "ExampleServerCluster", vpc=vpc)

        # Deploy MCP Server Service + Public Load Balancer
        mcp_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, "ExampleMcpServerService",
            cluster=cluster,
            cpu=256,  # 0.25 vCPU
            memory_limit_mib=512,  # 512MB RAM
            desired_count=1,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_asset("./examples/server/"),  # Build from local Dockerfile
                container_port=80,
            ),
            public_load_balancer=True,
            assign_public_ip=True,  # Ensure public IP is assigned to ECS task
            runtime_platform=ecs.RuntimePlatform(
                operating_system_family=ecs.OperatingSystemFamily.LINUX,
                cpu_architecture=ecs.CpuArchitecture.ARM64  # ARM64
            )
        )
        # Configure health check for MCP server
        mcp_service.target_group.configure_health_check(path='/health')

        # Output the Load Balancer URL after deploy
        self.mcp_server_dns_name = mcp_service.load_balancer.load_balancer_dns_name

        CfnOutput(self, "McpServerLoadBalancerDNS",
            value=mcp_service.load_balancer.load_balancer_dns_name,
            description="The DNS name of the load balancer for the Example MCP Server"
        )

        # Create Fargate Task Definition
        task_definition = ecs.FargateTaskDefinition(self, "ClientTaskDefinition",
            cpu=256,  # 0.25 vCPU
            memory_limit_mib=512,  # 512MB RAM
        )

        # Add container to the task definition
        task_definition.add_container(
            "ClientContainer",
            image=ecs.ContainerImage.from_asset("./examples/client/"),  # Build from Dockerfile in 'client' folder
            container_port=80,
            environment={  # Add any necessary environment variables here
            }
        )

        # Deploy the Client Service (without Load Balancer)
        client_service = ecs.FargateService(
            self, "ExampleMcpClientService",
            cluster=cluster,
            task_definition=task_definition,  # Attach the task definition
            assign_public_ip=True,  # Ensure public IP is assigned to ECS task
            runtime_platform=ecs.RuntimePlatform(
                operating_system_family=ecs.OperatingSystemFamily.LINUX,
                cpu_architecture=ecs.CpuArchitecture.ARM64  # ARM64
            )
        )

        # Output the Client Service DNS (for testing)
        CfnOutput(self, "ClientServiceDNS",
            value=f"http://{client_service.load_balancer.load_balancer_dns_name}",
            description="The DNS name of the client service"
        )
