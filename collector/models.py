from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class RawItem:
    source_name: str
    external_id: str
    title: str
    url: Optional[str] = None
    description: Optional[str] = None
    published_at: Optional[datetime] = None
