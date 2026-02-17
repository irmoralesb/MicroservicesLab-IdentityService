from dataclasses import dataclass
from uuid import UUID
import datetime


@dataclass
class UserServiceModel:
    id: UUID | None
    user_id: UUID
    service_id: UUID
    assigned_at: datetime.datetime | None = None
