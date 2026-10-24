from uuid import uuid4


class UuidGenerator:
    def new_id(self) -> str:
        return str(uuid4())
