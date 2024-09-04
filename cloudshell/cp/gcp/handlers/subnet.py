from __future__ import annotations

import logging
from contextlib import suppress
from functools import cached_property
from typing import TYPE_CHECKING

from attrs import define
from google.api_core.exceptions import NotFound
from google.cloud import compute_v1

from cloudshell.cp.gcp.handlers.base import BaseGCPHandler

# if TYPE_CHECKING:

logger = logging.getLogger(__name__)


@define
class SubnetHandler(BaseGCPHandler):
    region: str

    @cached_property
    def subnet_client(self):
        return compute_v1.SubnetworksClient(credentials=self.credentials)

    def get_or_create_subnet(
        self,
        network_name: str,
        subnet_name: str,
        ip_cidr_range: str,
        region: str = None,
    ) -> str:
        """Get subnet by its name or create a new one."""
        with suppress(NotFound):
            subnet = self.get_subnet_by_name(subnet_name, region)
            if subnet:
                logger.info(f"Subnet '{subnet}' already exists.")
                return subnet
        return self.create(network_name, subnet_name, ip_cidr_range, region)

    def list_subnets_by_network(self, network_name: str, region: str = None) -> list:
        """List all subnets in a network."""
        if not region:
            region = self.region
        # request = google.cloud.compute_v1.types.ListSubnetworksRequest(
        #     filter=f"network={full_network_name}",
        #     region=region,
        #     project=self.credentials.project_id
        # )
        return [x for x in self.subnet_client.list(
            project=self.credentials.project_id,
            region=region
        ) if x.network.split('/')[-1] == network_name]

    def create(
        self,
        network_name: str,
        subnet_name: str,
        ip_cidr_range: str,
        region: str = None,
    ) -> str:
        """"""
        if not region:
            region = self.region
        # Define the subnet settings
        subnet = compute_v1.Subnetwork()
        subnet.name = subnet_name
        subnet.ip_cidr_range = ip_cidr_range
        subnet.network = (
            f"projects/{self.credentials.project_id}/global/networks/{network_name}"
        )
        subnet.region = region

        # Create the subnet
        operation = self.subnet_client.insert(
            project=self.credentials.project_id,
            region=region,
            subnetwork_resource=subnet,
        )

        # Wait for the operation to complete
        # self.wait_for_operation(name=operation.name)
        self.wait_for_operation(name=operation.name, region=region)

        logger.info(f"Subnet '{subnet_name}' created successfully.")
        return self.get_subnet_by_name(subnet_name, region)

    def get_subnet_by_name(self, subnet_name: str, region: str = None) -> str:
        """"""
        logger.info("Getting subnet")
        if not region:
            region = self.region
        return self.subnet_client.get(
            project=self.credentials.project_id, region=region, subnetwork=subnet_name
        ).name

    def delete(self, subnet_name: str, region: str = None) -> None:
        """Tru to delete subnet by its name."""
        if not region:
            region = self.region

        operation = self.subnet_client.delete(
            project=self.credentials.project_id, region=region, subnetwork=subnet_name
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, region=region)
        # self.wait_for_operation(name=operation.name, region=region)

        logger.info(f"Subnet '{subnet_name}' deleted successfully.")
