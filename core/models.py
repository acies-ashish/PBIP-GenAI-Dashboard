from typing import List, Optional, Literal
from pydantic import BaseModel

class VisualIntent(BaseModel):
    """Abstract IR: Produced by LLM Planner. Contains ZERO physical schema info."""
    title: str
    visual_type: Literal["table", "bar", "column", "line", "card", "pie"]
    concepts: List[str]
    top_n: Optional[int] = None

class PhysicalBinding(BaseModel):
    concept_name: str
    table: str
    column: str
    kind: Literal["dimension", "measure"]
    data_type: Optional[str] = None
    aggregation: Optional[str] = None

class BoundVisual(BaseModel):
    """Final Materialization Spec: Fully resolved and validated."""
    visual_name: str
    visual_type: str
    bindings: List[PhysicalBinding]
    title: str
    top_n: Optional[int] = None