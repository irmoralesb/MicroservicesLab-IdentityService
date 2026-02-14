from uuid import UUID

class ServiceNotFoundError(Exception):

    def __init__(self, service_id: UUID | None) -> None:
        self.service_id = service_id
        super().__init__(f"No service found for service id: '{service_id}'.")

class ServiceNameNotFoundError(Exception):

    def __init__(self, service_name: str | None) -> None:
        self.service_name = service_name
        super().__init__(f"No service found for service name: '{service_name}'.")


class ServiceCreationError(Exception):

    def __init__(self, service_name: str | None) -> None:
        self.service_name = service_name
        super().__init__(f"Error creating service {service_name}")


class ServiceUpdateError(Exception):

    def __init__(self, service_name: str) -> None:
        self.service_name = service_name
        super().__init__(f"Error updating service {service_name}")

class ServiceDataAccessError(Exception):

    def __init__(self) -> None:
        super().__init__("There is an error accessing the database.")