from __future__ import annotations

from contextlib import suppress

from attr import define
from cloudshell.cp.core.flows.cleanup_sandbox_infra import \
    AbstractCleanupSandboxInfraFlow
from cloudshell.cp.core.request_actions.models import CleanupNetwork
from google.api_core.exceptions import NotFound
from typing_extensions import TYPE_CHECKING

from cloudshell.cp.gcp.handlers.firewall_rule import FirewallRuleHandler
from cloudshell.cp.gcp.handlers.ssh_keys import SSHKeysHandler
from cloudshell.cp.gcp.handlers.subnet import SubnetHandler
from cloudshell.cp.gcp.handlers.vpc import VPCHandler
from cloudshell.cp.core.request_actions import CleanupSandboxInfraRequestActions

from cloudshell.cp.gcp.helpers.name_generator import GCPNameGenerator

if TYPE_CHECKING:
    from logging import Logger
    from cloudshell.cp.gcp.resource_conf import GCPResourceConfig


@define
class CleanUpGCPInfraFlow(AbstractCleanupSandboxInfraFlow):
    logger: Logger
    config: GCPResourceConfig

    def __attrs_post_init__(self):
        super().__init__(self.logger)

    def cleanup_sandbox_infra(self, request_actions: CleanupSandboxInfraRequestActions):
        if request_actions.cleanup_network:
            self._cleanup_network(request_actions.cleanup_network)

    def _cleanup_network(self, cleanup_network_action: CleanupNetwork):
        sandbox_id = self.config.reservation_info.reservation_id
        storage_handler = SSHKeysHandler(self.config.credentials)
        network_name = GCPNameGenerator().network(sandbox_id)
        self._logger.info(f"Cleaning up network: quali{network_name} in region:"
                          f" {self.config.region}")

        # Delete VPC components
        storage_handler.delete_ssh_keys(
            bucket_name=self.config.keypairs_location,
            folder_path=sandbox_id
        )
        self.delete_vpc_components(network_name)

    def delete_vpc_components(self, network_name: str) -> None:
        """Delete all components of a VPC."""
        self.logger.info(f"Deleting all components of VPC: {network_name}")

        # try:
        network_handler = VPCHandler.get_vpc_by_sandbox_id(
            self.config.reservation_info.reservation_id,
            self.config.credentials
        )
        vpc = network_handler.network

        # Get subnets
        subnets = {x.split("/")[-1] for x in vpc.subnetworks}
        subnet_handler = SubnetHandler(self.config.credentials, self.config.region)
        if not subnets:
            subnets = {x.name for x in subnet_handler.list_subnets_by_network(
                network_name
                )
            }
        # Delete subnets
        for subnet in subnets:
            self.logger.info(f"Deleting subnet: {subnet}")
            subnet_handler.delete(subnet_name=subnet)

        # Delete firewall rules
        firewall_handler = FirewallRuleHandler(self.config.credentials)
        for rule in firewall_handler.list_firewall_rules_by_network(network_name):
            self.logger.info(f"Deleting firewall rule: {rule.name}")
            firewall_handler.delete(rule_name=rule.name)

        # Delete routes
        # routes = self.route_client.list(project=self.credentials.project_id, filter=f"network={network_name}")
        # for route in routes:
        #     self.logger.info(f"Deleting route: {route.name}")
        #     operation = self.route_client.delete(project=self.credentials.project_id, route=route.name)
        #     self.wait_for_operation(name=operation.name)

        network_handler.delete()

        with suppress(NotFound):
            VPCHandler.get_vpc_by_sandbox_id(
                self.config.reservation_info.reservation_id,
                self.config.credentials
            )
            raise Exception(f"Failed to delete VPC '{network_name}'.")

        self.logger.info(f"All components of VPC '{network_name}' deleted "
                         f"successfully.")
