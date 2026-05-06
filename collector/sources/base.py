from abc import ABC, abstractmethod

import httpx

from models import RawItem


class BaseSource(ABC):
    @property
    @abstractmethod
    def source_name(self) -> str: ...

    @abstractmethod
    async def fetch(self, client: httpx.AsyncClient) -> list[RawItem]: ...
