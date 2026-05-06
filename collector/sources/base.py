from abc import ABC, abstractmethod

import httpx

from models import RawItem


class BaseSource(ABC):
    source_name: str

    @abstractmethod
    async def fetch(self, client: httpx.AsyncClient) -> list[RawItem]:
        ...
