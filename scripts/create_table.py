"""Create the tasks table (idempotent). Reads the same env vars as the service."""

import boto3
from botocore.exceptions import ClientError

from src.infrastructure.dynamo_table import create_tasks_table
from src.infrastructure.settings import Settings


def main() -> None:
    settings = Settings()
    dynamodb = boto3.resource(
        "dynamodb",
        region_name=settings.aws_region,
        endpoint_url=settings.dynamodb_endpoint_url,
    )
    try:
        create_tasks_table(dynamodb, settings.tasks_table_name)
    except ClientError as error:
        if error.response["Error"]["Code"] != "ResourceInUseException":
            raise
        print(f"Table {settings.tasks_table_name} already exists")
        return
    print(f"Created table {settings.tasks_table_name}")


if __name__ == "__main__":
    main()
