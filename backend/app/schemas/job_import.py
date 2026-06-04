from pydantic import BaseModel, Field, HttpUrl


class JobImportRequest(BaseModel):
    url: HttpUrl


class JobImportConfidence(BaseModel):
    company: float = Field(ge=0, le=1)
    title: float = Field(ge=0, le=1)
    location: float = Field(ge=0, le=1)
    salary: float = Field(ge=0, le=1)
    deadline: float = Field(ge=0, le=1)
    description: float = Field(ge=0, le=1)


class JobImportResult(BaseModel):
    source: str
    company: str | None = None
    title: str | None = None
    location: str | None = None
    salary: str | None = None
    deadline: str | None = None
    description: str
    confidence: JobImportConfidence
    warnings: list[str] = Field(default_factory=list)
    raw_url: str


class LLMJobPageExtraction(BaseModel):
    company: str | None = None
    title: str | None = None
    location: str | None = None
    salary: str | None = None
    deadline: str | None = None
    description: str | None = None
    confidence: JobImportConfidence
    warnings: list[str] = Field(default_factory=list)
