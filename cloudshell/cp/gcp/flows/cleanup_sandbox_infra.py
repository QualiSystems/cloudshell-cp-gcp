from __future__ import annotations

from cloudshell.cp.core.flows.cleanup_sandbox_infra import AbstractCleanupSandboxInfraFlow
from cloudshell.cp.core.request_actions.models import CleanupNetwork
from typing_extensions import TYPE_CHECKING

from cloudshell.cp.gcp.handlers.ssh_keys import SSHKeysHandler
from cloudshell.cp.gcp.handlers.vpc import VPCHandler
from cloudshell.cp.gcp.helpers.name_generator import generate_vpc_name


from cloudshell.cp.core.request_actions import CleanupSandboxInfraRequestActions

if TYPE_CHECKING:
    from cloudshell.cp.gcp.resource_conf import GCPResourceConfig


class CleanUpGCPInfraFlow(AbstractCleanupSandboxInfraFlow):
    def __init__(self, logger, resource_config: GCPResourceConfig):
        super().__init__(logger)
        self.config = resource_config

    def cleanup_sandbox_infra(self, request_actions: CleanupSandboxInfraRequestActions):
        if request_actions.cleanup_network:
            self._cleanup_network(request_actions.cleanup_network)

    def _cleanup_network(self, cleanup_network_action: CleanupNetwork):
        sandbox_id = self.config.reservation_info.reservation_id
        storage_handler = SSHKeysHandler(self.config.credentials)
        network_name = generate_vpc_name(sandbox_id)
        self._logger.info(f"Cleaning up network: quali{network_name} in region:"
                          f" {self.config.region}")

        network_handler = VPCHandler(self.config.credentials)
        network_handler.delete(network_name=network_name)
        storage_handler.delete_ssh_keys(
            bucket_name=self.config.keypairs_location,
            folder_path=sandbox_id
        )
