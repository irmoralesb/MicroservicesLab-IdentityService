class ServiceNotFoundException(Exception):

    def __init__(self, service_name: str | None) -> None:
        self.service_name = service_name
        super().__init__(f"Service '{service_name}' not found")