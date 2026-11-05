from pydantic import BaseModel, Field

from app.enums import RecyclabilityStatus
from app.schemas.common import ORMModel


class RuleCreate(BaseModel):
    title: str = Field(min_length=2, max_length=150)
    description: str = Field(min_length=3)
    container_color: str | None = None


class RuleOut(ORMModel):
    id: int
    waste_category_id: int
    title: str
    description: str
    container_color: str | None


class CategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    code: str = Field(min_length=2, max_length=20)
    classification: str | None = None
    description: str | None = None
    recyclability: RecyclabilityStatus = RecyclabilityStatus.RECYCLABLE
    disposal_instructions: str | None = None
    is_hazardous: bool = False


class CategoryUpdate(BaseModel):
    classification: str | None = None
    description: str | None = None
    recyclability: RecyclabilityStatus | None = None
    disposal_instructions: str | None = None
    is_hazardous: bool | None = None
    is_active: bool | None = None


class CategoryOut(ORMModel):
    id: int
    name: str
    code: str
    classification: str | None
    description: str | None
    recyclability: RecyclabilityStatus
    disposal_instructions: str | None
    is_hazardous: bool
    is_active: bool
    segregation_rules: list[RuleOut] = []
