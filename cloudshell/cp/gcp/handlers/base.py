from __future__ import annotations

import random
from typing import TYPE_CHECKING

from attrs import define
from google.api_core import gapic_v1
from google.cloud import compute_v1

if TYPE_CHECKING:
    from google.auth.credentials import Credentials
    from google.cloud.compute_v1.types import compute


@define
class BaseGCPHandler:
    credentials: Credentials

    def wait_for_operation(
        self,
        name: str,
        region: str = None,
        zone: str = None,
        timeout: float = gapic_v1.method.DEFAULT,
    ) -> None:
        wait_attributes = {
            "project": self.credentials.project_id,
            "operation": name,
            "timeout": timeout,
        }
        if zone:
            operation_client = compute_v1.ZoneOperationsClient(
                credentials=self.credentials
            )
            wait_attributes["zone"] = zone
        elif region:
            operation_client = compute_v1.RegionOperationsClient(
                credentials=self.credentials
            )
            wait_attributes["region"] = region
        else:
            operation_client = compute_v1.GlobalOperationsClient(
                credentials=self.credentials
            )

        operation_client.wait(**wait_attributes)

    def get_regions(self) -> list[compute.Region]:
        """Retrieves the list of Region resources available to the specified project."""
        client = compute_v1.RegionsClient(credentials=self.credentials)
        request = compute_v1.ListRegionsRequest(project=self.credentials.project_id)
        regions = client.list(request=request)

        return list(regions)

    def get_zones(self, region: str = None) -> list[compute.Zone]:
        """Retrieves the list of Zone resources available to the specified project.

        Can be filtered by region.
        """
        client = compute_v1.ZonesClient(credentials=self.credentials)
        request = compute_v1.ListZonesRequest(project=self.credentials.project_id)
        zones = client.list(request=request)

        if region:
            zones = [zone for zone in zones if zone.region.endswith(region)]

        return list(zones)
