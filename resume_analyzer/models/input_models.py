from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

class ResumeEvent(BaseModel):
    model_config = ConfigDict(extra='ignore')
    type: str = Field(...)
    title: Optional[str] = Field(default=None)
    level: Optional[str] = Field(default=None)
    start_date: Optional[str] = Field(default=None)
    end_date: Optional[str] = Field(default=None)
    payload: dict[str, Any] = Field(default_factory=dict)

    @field_validator("type", "title", "level", mode="before")
    @classmethod
    def normalize_strings(cls, value: Any) -> Optional[str]:
        if value is None:
            return None
        return str(value).strip().lower()

class ResumeInput(BaseModel):
    events: list[ResumeEvent] = Field(default_factory=list)