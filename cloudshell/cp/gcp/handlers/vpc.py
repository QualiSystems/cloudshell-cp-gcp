from __future__ import annotations

import logging

from google.cloud import compute_v1
from functools import cached_property
from typing import TYPE_CHECKING

from cloudshell.cp.gcp.handlers.base import BaseGCPHandler


# if TYPE_CHECKING:

logger = logging.getLogger(__name__)


class VPCHandler(BaseGCPHandler):

    @cached_property
    def network_client(self):
        return compute_v1.NetworksClient(credentials=self.credentials)

    def get_vpc_by_name(self, network_name):
        logger.info("Getting VPC")
        return self.network_client.get(project=self.project_id, network=network_name)

    def get_vpc_by_sandbox_id(self, sandbox_id):
        tag_name = "sandbox_id"
        logger.info("Getting VPC")
        networks = self.network_client.list(project=self.project_id)

        # Filter networks by label
        for network in networks:
            if network.labels and network.labels.get(tag_name) == sandbox_id:
                return network

    def create(self, network_name):

        # Define the VPC network settings
        network = compute_v1.Network()
        network.name = network_name
        network.auto_create_subnetworks = False  # We will create custom subnets

        # Create the VPC network
        operation = self.network_client.insert(
            project=self.project_id,
            network_resource=network
        )

        # Wait for the operation to complete
        operation_client = compute_v1.GlobalOperationsClient()
        operation_client.wait(project=self.project_id, operation=operation.name)

        print(f"VPC network '{network_name}' created successfully.")

    def delete(self, network_name):
        operation = self.network_client.delete(project=self.project_id,
                                                network=network_name)

        # Wait for the operation to complete
        operation_client = compute_v1.GlobalOperationsClient()
        operation_client.wait(project=self.project_id, operation=operation.name)

        print(f"VPC network '{network_name}' deleted successfully.")
