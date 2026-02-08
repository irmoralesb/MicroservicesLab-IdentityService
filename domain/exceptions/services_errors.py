from uuid import UUID

class ServiceNotFoundError(Exception):

    def __init__(self, service_name: UUID | None) -> None:
        self.service_name = service_name
        super().__init__(f"No service found for Service id '{service_name}'.")


class ServiceCreationError(Exception):

    def __init__(self, service_name: str | None) -> None:
        self.service_name = service_name
        super().__init__(f"Error creating service {service_name}")


class ServiceUpdateError(Exception):

    def __init__(self, service_id: UUID) -> None:
        self.service_id = service_id
        super().__init__(f"Error updating service for Service id {service_id}")