from pydantic import BaseModel, Field


class ChartPoint(BaseModel):
    label: str
    value: float


class ChartResponse(BaseModel):
    points: list[ChartPoint]
    unit: str | None = None
    source: str


class ResearchQuestion(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class MaterialComparisonRequest(BaseModel):
    materials: list[str] = Field(min_length=2, max_length=10)
