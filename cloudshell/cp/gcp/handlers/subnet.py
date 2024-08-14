from __future__ import annotations

import logging

from google.cloud import compute_v1
from functools import cached_property
from google.oauth2 import service_account

from cloudshell.cp.gcp.handlers.base import BaseGCPHandler


# if TYPE_CHECKING:

logger = logging.getLogger(__name__)


class SubnetHandler(BaseGCPHandler):
    @cached_property
    def subnet_client(self):
        return compute_v1.SubnetworksClient(credentials=self.credentials)

    def create(self, network_name, subnet_name, region, ip_cidr_range):
        # Define the subnet settings
        subnet = compute_v1.Subnetwork()
        subnet.name = subnet_name
        subnet.ip_cidr_range = ip_cidr_range
        subnet.network = f"projects/{self.project_id}/global/networks/{network_name}"
        subnet.region = region

        # Create the subnet
        operation = self.subnet_client.insert(
            project=self.project_id,
            region=region,
            subnetwork_resource=subnet
        )

        # Wait for the operation to complete
        operation_client = compute_v1.GlobalOperationsClient()
        operation_client.wait(project=self.project_id, operation=operation.name)

        print(f"Subnet '{subnet_name}' created successfully.")
        return self.get_subnet_by_name(subnet_name, region).id

    def get_subnet_by_name(self, subnet_name, region):
        logger.info("Getting subnet")
        return self.subnet_client.get(project=self.project_id, region=region, subnetwork=subnet_name)

    def delete(self, subnet_name, region):
        operation = self.subnet_client.delete(project=self.project_id, region=region, subnetwork=subnet_name)

        # Wait for the operation to complete
        operation_client = compute_v1.GlobalOperationsClient()
        operation_client.wait(project=self.project_id, operation=operation.name)

        print(f"Subnet '{subnet_name}' deleted successfully.")
