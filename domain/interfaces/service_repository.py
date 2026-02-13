from abc import ABC, abstractmethod
from domain.entities.service_model import ServiceModel
from typing import List
import uuid

class ServiceRepositoryInterface(ABC):
    """Abstract base class defining the interface for user repository operations"""

    @abstractmethod
    async def get_all(self)-> List[ServiceModel]:
        pass

    @abstractmethod
    async def get_by_id(self, service_id: uuid.UUID) -> ServiceModel | None:
        pass

    @abstractmethod
    async def get_by_name(self, service_name: str) -> ServiceModel | None:
        pass

    @abstractmethod
    async def create_service(self, service: ServiceModel) -> ServiceModel:
        pass

    @abstractmethod
    async def update_service(self, service: ServiceModel) -> ServiceModel:
        pass

    @abstractmethod
    async def get_by_ids(self, service_ids: List[uuid.UUID]) -> List[ServiceModel]:
        pass

