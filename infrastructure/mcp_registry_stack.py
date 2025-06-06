from aws_cdk import Stack, Duration, RemovalPolicy
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_iam as iam
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_logs as logs
from aws_cdk import aws_ecs_patterns as ecs_patterns
from aws_cdk import aws_opensearchservice as opensearch
from aws_cdk import aws_s3 as s3
from constructs import Construct

class McpRegistryStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        # Create a VPC (use 2 AZs for availability)
        vpc = ec2.Vpc(self, "McpRegistryVpc",
            max_azs=2,
            nat_gateways=0,  # No NAT Gateway
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                )
            ]
        )
        # --- DynamoDB Table for MCP Servers
        servers_table = dynamodb.Table(
            self, 
            "McpServersTable",
            partition_key=dynamodb.Attribute(
                name="id", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,  # Cost effective
            removal_policy=RemovalPolicy.DESTROY  # NOTE: DESTROY for dev; change for prod
        )

        # --- ECS Cluster
        cluster = ecs.Cluster(self, "McpRegistryCluster", vpc=vpc)

        # --- ECS Service (Fargate) for MCP Registry API
        mcp_registry_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "McpRegistryFargateService",
            cluster=cluster,
            cpu=512,
            memory_limit_mib=1024,
            desired_count=1,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_asset(
                    directory="./",              # Full project root
                    file="code/Dockerfile"        # Relative path to Dockerfile
                ),
                container_port=80,
                environment={
                    "DYNAMODB_TABLE_NAME": servers_table.table_name,
                    "AWS_REGION": Stack.of(self).region,
                    "RUN_LOCAL": "False"
                },
                log_driver=ecs.LogDrivers.aws_logs(
                    stream_prefix="McpRegistry",
                    log_group=logs.LogGroup(self, "McpRegistryLogGroup")
                )
            ),
            public_load_balancer=True,
            assign_public_ip=True,
            runtime_platform=ecs.RuntimePlatform(
                operating_system_family=ecs.OperatingSystemFamily.LINUX,
                cpu_architecture=ecs.CpuArchitecture.ARM64
            )
        )
        # Grant ECS Service permissions to DDB + S3
        servers_table.grant_read_write_data(mcp_registry_service.task_definition.task_role)
        mcp_registry_service.target_group.configure_health_check(path='/health')

        

