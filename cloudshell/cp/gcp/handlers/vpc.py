from __future__ import annotations

import logging
from contextlib import suppress
from functools import cached_property
from typing import TYPE_CHECKING

from google.api_core.exceptions import NotFound
from google.cloud import compute_v1

from cloudshell.cp.gcp.handlers.base import BaseGCPHandler

if TYPE_CHECKING:
    from google.cloud.compute_v1.types import compute

logger = logging.getLogger(__name__)


class VPCHandler(BaseGCPHandler):
    @cached_property
    def network_client(self):
        return compute_v1.NetworksClient(credentials=self.credentials)

    def get_vpc_by_name(self, network_name: str) -> compute.Network:
        """Get VPC instance by its name."""
        logger.info("Getting VPC")
        return self.network_client.get(
            project=self.credentials.project_id, network=network_name
        )

    def get_vpc_by_sandbox_id(self, sandbox_id: str) -> compute.Network:
        """Get VPC instance by tag Sandbox ID."""
        logger.info("Getting VPC")
        tag_name = "sandbox_id"
        networks = self.network_client.list(project=self.credentials.project_id)

        # Filter networks by label
        for network in networks:
            if network.labels and network.labels.get(tag_name) == sandbox_id:
                return network

    def get_or_create_vpc(self, sandbox_id: str) -> str:
        """Get VPC by Sandbox ID or create a new one."""
        with suppress(NotFound):
            vpc = self.get_vpc_by_name(sandbox_id)
            if vpc:
                logger.info(f"VPC network '{vpc.name}' already exists.")
                return vpc.name
        return self.create(sandbox_id)

    def create(self, network_name: str) -> str:
        """Create VPC."""
        # Define the VPC network settings
        network = compute_v1.Network()
        network.name = network_name
        network.auto_create_subnetworks = False  # We will create custom subnets

        # Create the VPC network
        operation = self.network_client.insert(
            project=self.credentials.project_id, network_resource=network
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name)

        logger.info(f"VPC network '{network.name}' created successfully.")
        return network.name

    def delete(self, network_name: str) -> None:
        operation = self.network_client.delete(
            project=self.credentials.project_id, network=network_name
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name)

        logger.info(f"VPC network '{network_name}' deleted successfully.")
