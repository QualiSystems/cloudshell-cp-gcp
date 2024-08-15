from __future__ import annotations

from attrs import define
from google.api_core import gapic_v1
from google.cloud import compute_v1

from typing_extensions import TYPE_CHECKING

if TYPE_CHECKING:
    from google.auth.credentials import Credentials


@define
class BaseGCPHandler:
    credentials: Credentials

    def wait_for_operation(
            self,
            name: str,
            region: str = None,
            zone: str = None,
            timeout: float=gapic_v1.method.DEFAULT
    ) -> None:
        wait_attributes = {
            "project": self.credentials.project_id,
            "operation": name,
            "timeout": timeout
        }
        if zone:
            operation_client = compute_v1.ZoneOperationsClient(credentials=self.credentials)
            wait_attributes["zone"] = zone
        elif region:
            operation_client = compute_v1.RegionOperationsClient(credentials=self.credentials)
            wait_attributes["region"] = region
        else:
            operation_client = compute_v1.GlobalOperationsClient(credentials=self.credentials)

        operation_client.wait(**wait_attributes)

    # def wait_to_complete(self, timeout: float):
    #     def decorator(func):
    #         def wrapper(*args, **kwargs):
    #             operation = func(*args, **kwargs)
    #
    #             wait_attributes = {
    #                 "project": self.credentials.project_id,
    #                 "operation": operation.name,
    #             }
    #
    #             if timeout:
    #                 wait_attributes["timeout"] = timeout
    #
    #             if "zone" in kwargs:
    #                 operation_client = compute_v1.ZoneOperationsClient()
    #                 wait_attributes["zone"] = kwargs["zone"]
    #             else:
    #                 operation_client = compute_v1.GlobalOperationsClient()
    #
    #             operation_client.wait(**wait_attributes)
    #
    #             return operation
    #         return wrapper
    #     return decorator
