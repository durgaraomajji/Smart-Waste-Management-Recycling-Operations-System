from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class MessageResponse(BaseModel):
    success: bool = True
    message: str


class DataResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T


def message(msg: str) -> dict[str, Any]:
    return {"success": True, "message": msg}
