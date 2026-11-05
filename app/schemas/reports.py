from datetime import date

from pydantic import BaseModel

from app.core.pagination import PageParams  # noqa: F401


class ReportRow(BaseModel):
    row: dict


class ReportResponse(BaseModel):
    report: str
    generated_for: dict
    total: int
    page: int
    page_size: int
    items: list[dict]
