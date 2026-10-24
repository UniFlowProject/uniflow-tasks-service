GSI_NAME = "user-period-index"
GSI_HASH_KEY = "user_id"
GSI_RANGE_KEY = "period_due_key"


def create_tasks_table(dynamodb, table_name: str):
    """Create the tasks table with its GSI and wait until it is active.

    `dynamodb` is a boto3 DynamoDB service resource.
    """
    table = dynamodb.create_table(
        TableName=table_name,
        BillingMode="PAY_PER_REQUEST",
        AttributeDefinitions=[
            {"AttributeName": "task_id", "AttributeType": "S"},
            {"AttributeName": GSI_HASH_KEY, "AttributeType": "S"},
            {"AttributeName": GSI_RANGE_KEY, "AttributeType": "S"},
        ],
        KeySchema=[{"AttributeName": "task_id", "KeyType": "HASH"}],
        GlobalSecondaryIndexes=[
            {
                "IndexName": GSI_NAME,
                "KeySchema": [
                    {"AttributeName": GSI_HASH_KEY, "KeyType": "HASH"},
                    {"AttributeName": GSI_RANGE_KEY, "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
    )
    table.wait_until_exists()
    return table
