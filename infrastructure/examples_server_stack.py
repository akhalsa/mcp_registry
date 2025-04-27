from aws_cdk import (
    Stack,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_ec2 as ec2,
    CfnOutput
)
from constructs import Construct

class ExampleMcpServerStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create a VPC (use 2 AZs for availability)
        vpc = ec2.Vpc(self, "ExampleServerVpc",
            max_azs=2,
            nat_gateways=0,  # <---- KEY LINE: NO NAT GATEWAY
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                )
            ]
        )


        # Create ECS Cluster
        cluster = ecs.Cluster(self, "ExampleServerCluster", vpc=vpc)

        # Deploy Fargate Service + Public Load Balancer
        service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, "ExampleMcpServerService",
            cluster=cluster,
            cpu=256,  # 0.25 vCPU
            memory_limit_mib=512,  # 512MB RAM
            desired_count=1,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_asset("./examples/server/"),  # Build from local Dockerfile
                container_port=80,
            ),
            public_load_balancer=True
        )

        # Output the Load Balancer URL after deploy
        self.load_balancer_dns_name = service.load_balancer.load_balancer_dns_name

        CfnOutput(self, "LoadBalancerDNS",
            value=service.load_balancer.load_balancer_dns_name,
            description="The DNS name of the load balancer for the Example MCP Server"
        )
