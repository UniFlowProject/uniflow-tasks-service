from typing import Annotated

from fastapi import Depends, Header

from src.domain.user import UserContext
from src.infrastructure.http.errors import UnauthorizedError
from src.infrastructure.http.headers import (
    USER_EMAIL_HEADER,
    USER_ID_HEADER,
    USER_NAME_HEADER,
    USER_PICTURE_HEADER,
)


def get_current_user(
    user_id: Annotated[str | None, Header(alias=USER_ID_HEADER)] = None,
    email: Annotated[str | None, Header(alias=USER_EMAIL_HEADER)] = None,
    name: Annotated[str | None, Header(alias=USER_NAME_HEADER)] = None,
    picture: Annotated[str | None, Header(alias=USER_PICTURE_HEADER)] = None,
) -> UserContext:
    if user_id is None or not user_id.strip():
        raise UnauthorizedError(f"Missing or empty {USER_ID_HEADER} header")
    return UserContext(id=user_id, email=email, name=name, picture=picture)


CurrentUser = Annotated[UserContext, Depends(get_current_user)]
