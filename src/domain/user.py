from pydantic import BaseModel, ConfigDict, Field


class UserContext(BaseModel):
    """Authenticated user, as identified by the upstream gateway.

    This service does not own users: identity arrives already verified, so
    the domain only needs to know who is calling.
    """

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    id: str = Field(min_length=1)
    email: str | None = None
    name: str | None = None
    picture: str | None = None
