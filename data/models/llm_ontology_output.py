from pydantic import BaseModel, Field
from typing import List, Optional


class Actor(BaseModel):
    name: str
    role: Optional[str] = Field(
        description="Role in the event (e.g. attacker, victim, government, military, civilian, etc.)"
    )


class ExtractedEventOutput(BaseModel):
    event_type: str
    subtype: str

    occurred_at: Optional[str]
    location: Optional[str]

    actors: List[Actor] = Field(default_factory=list)

    fatalities: Optional[int]
    injured: Optional[int]

    weapons: List[str] = Field(default_factory=list)

    confidence: float = Field(ge=0.0, le=1.0)

    source_url: str
