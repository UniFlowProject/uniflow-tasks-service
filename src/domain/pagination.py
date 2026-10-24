from math import ceil

from pydantic import BaseModel


class PageInfo(BaseModel):
    total: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool

    @classmethod
    def of(cls, total: int, page: int, limit: int) -> "PageInfo":
        total_pages = ceil(total / limit)
        return cls(
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1 and total_pages > 0,
        )
    