from __future__ import annotations

import logging

from attrs import define
from typing_extensions import TYPE_CHECKING
from functools import cached_property
from google.cloud import compute_v1

from cloudshell.cp.gcp.handlers.base import BaseGCPHandler


if TYPE_CHECKING:
    from google.cloud.compute_v1.types import compute

logger = logging.getLogger(__name__)


@define
class SubnetHandler(BaseGCPHandler):
    region: str

    @cached_property
    def subnet_client(self):
        return compute_v1.SubnetworksClient(credentials=self.credentials)

    def create(
            self,
            network_name: str,
            subnet_name: str,
            ip_cidr_range: str,
            region: str = None
    ) -> str:
        """"""
        if not region:
            region = self.region
        # Define the subnet settings
        subnet = compute_v1.Subnetwork()
        subnet.name = subnet_name
        subnet.ip_cidr_range = ip_cidr_range
        subnet.network = f"projects/{self.credentials.project_id}/global/networks/{network_name}"
        subnet.region = region

        # Create the subnet
        operation = self.subnet_client.insert(
            project=self.credentials.project_id,
            region=region,
            subnetwork_resource=subnet
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name)
        # self.wait_for_operation(name=operation.name, region=region)

        logger.info(f"Subnet '{subnet_name}' created successfully.")
        return self.get_subnet_by_name(subnet_name, region).id

    def get_subnet_by_name(self, subnet_name: str, region: str) -> compute.Subnetwork:
        """"""
        logger.info("Getting subnet")
        return self.subnet_client.get(project=self.credentials.project_id, region=region, subnetwork=subnet_name)

    def delete(self, subnet_name: str, region: str = None) -> None:
        """Tru to delete subnet by its name."""
        if not region:
            region = self.region

        operation = self.subnet_client.delete(
            project=self.credentials.project_id,
            region=region,
            subnetwork=subnet_name
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name)
        # self.wait_for_operation(name=operation.name, region=region)

        logger.info(f"Subnet '{subnet_name}' deleted successfully.")
