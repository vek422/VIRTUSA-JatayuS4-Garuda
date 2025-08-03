from abc import ABC, abstractmethod

class IAuthService(ABC):
    @abstractmethod
    async def login(self, email: str, password: str, db) -> dict:
        pass

    @abstractmethod
    async def signup(self, data: dict, db) -> str:
        pass
