from __future__ import annotations

import logging
from contextlib import suppress
from functools import cached_property
from typing import TYPE_CHECKING, Self

from attr import define
from google.api_core.exceptions import NotFound
from google.cloud import compute_v1

from cloudshell.cp.gcp.handlers.base import BaseGCPHandler
from cloudshell.cp.gcp.helpers.name_generator import GCPNameGenerator

if TYPE_CHECKING:
    from google.cloud.compute_v1.types import compute

logger = logging.getLogger(__name__)

@define
class VPCHandler(BaseGCPHandler):
    network: compute.Network

    @cached_property
    def network_client(self):
        return compute_v1.NetworksClient(credentials=self.credentials)

    @classmethod
    def get_vpc_by_name(cls, network_name: str, credentials: compute.Credentials) -> Self:
        """Get VPC instance by its name."""
        logger.info("Getting VPC")
        network_client = compute_v1.NetworksClient(credentials=credentials)
        network = network_client.get(
            project=credentials.project_id, network=network_name
        )
        return cls(
            credentials=credentials,
            network=network
        )

    @classmethod
    def get_vpc_by_sandbox_id(
            cls,
            sandbox_id: str,
            credentials: compute.Credentials
    ) -> Self:
        """Get VPC instance by Sandbox ID."""
        logger.info("Getting VPC")
        network_name = GCPNameGenerator().network(sandbox_id)
        network = cls.get_vpc_by_name(network_name, credentials)
        return network

    @classmethod
    def get_or_create_vpc(self, sandbox_id: str, credentials: compute.Credentials) -> Self:
        """Get VPC by Sandbox ID or create a new one."""
        with suppress(NotFound):
            vpc = self.get_vpc_by_sandbox_id(sandbox_id, credentials)
            if vpc:
                return vpc
        return self.create(sandbox_id, credentials)

    @classmethod
    def create(cls, network_name: str, credentials: compute.Credentials) -> Self:
        """Create VPC."""
        network_client = compute_v1.NetworksClient(credentials=credentials)
        # Define the VPC network settings
        network = compute_v1.Network()
        network.name = network_name
        network.auto_create_subnetworks = False  # We will create custom subnets

        # Create the VPC network
        operation = network_client.insert(
            project=credentials.project_id, network_resource=network
        )

        # Wait for the operation to complete
        operation_client = compute_v1.GlobalOperationsClient(
            credentials=credentials
        )

        operation_client.wait(operation=operation.name)

        logger.info(f"VPC network '{network.name}' created successfully.")
        return cls(credentials, network)

    def delete(self) -> None:
        operation = self.network_client.delete(
            project=self.credentials.project_id, network=self.network.name
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name)

        logger.info(f"VPC network '{self.network.name}' deleted successfully.")

    def get_subnets(self):
        return list(self.network.subnetworks)
