from src.infrastructure.settings import RepositoryKind, Settings


def test_defaults_to_memory_repository(monkeypatch):
    monkeypatch.delenv("TASKS_REPOSITORY", raising=False)

    settings = Settings()

    assert settings.tasks_repository == RepositoryKind.MEMORY
    assert settings.dynamodb_endpoint_url is None


def test_reads_environment(monkeypatch):
    monkeypatch.setenv("TASKS_REPOSITORY", "dynamodb")
    monkeypatch.setenv("TASKS_TABLE_NAME", "my-tasks")
    monkeypatch.setenv("AWS_REGION", "eu-west-1")
    monkeypatch.setenv("DYNAMODB_ENDPOINT_URL", "http://localhost:8000")

    settings = Settings()

    assert settings.tasks_repository == RepositoryKind.DYNAMODB
    assert settings.tasks_table_name == "my-tasks"
    assert settings.aws_region == "eu-west-1"
    assert settings.dynamodb_endpoint_url == "http://localhost:8000"
