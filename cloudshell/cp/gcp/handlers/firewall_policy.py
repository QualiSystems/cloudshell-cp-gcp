from __future__ import annotations

import logging
from functools import cached_property
from typing import TYPE_CHECKING

from google.cloud import compute_v1

from cloudshell.cp.gcp.handlers.base import BaseGCPHandler

if TYPE_CHECKING:
    from google.cloud.compute_v1.types import compute

logger = logging.getLogger(__name__)


class FirewallPolicyHandler(BaseGCPHandler):
    @cached_property
    def firewall_client(self):
        return compute_v1.FirewallsClient(credentials=self.credentials)

    def create(self, security_group_name: str, network_name: str, rules) -> str:
        """"""
        # Define the firewall settings
        firewall = compute_v1.Firewall()
        firewall.name = security_group_name
        firewall.network = (
            f"projects/{self.credentials.project_id}/global/networks/{network_name}"
        )
        firewall.allowed = rules

        # Create the firewall
        operation = self.firewall_client.insert(
            project=self.credentials.project_id, firewall_resource=firewall
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name)

        logger.info(f"Security group '{security_group_name}' created successfully.")
        return self.get_security_group_by_name(security_group_name).id

    def get_firewall_policy_by_name(self, security_group_name: str) -> (
            compute_v1.Firewall):
        """Get Security Group instance by its name."""
        logger.info("Getting security group")
        return self.firewall_client.get(
            project=self.credentials.project_id, firewall=security_group_name
        )

    def delete(self, security_group_name: str) -> None:
        """Delete Security Group."""
        operation = self.firewall_client.delete(
            project=self.credentials.project_id, firewall=security_group_name
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name)

        logger.info(f"Security group '{security_group_name}' deleted successfully.")

    def add_rule(self, policy_name: str, protocol: str, ports: list[int]) -> None:
        """Add a new rule to an existing firewall policy."""
        # Get the existing firewall policy
        firewall_policy = self.get_firewall_policy_by_name(policy_name)

        new_rule = {
            "IPProtocol": protocol,
            "ports": list(map(str, ports)),
        }

        # Add the new rule
        new_allowed_rule = compute_v1.Firewall.Allowed.from_dict(new_rule)
        firewall_policy.allowed.append(new_allowed_rule)

        # Update the firewall policy
        operation = self.firewall_client.patch(
            project=self.credentials.project_id,
            firewall=policy_name,
            firewall_resource=firewall_policy,
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name)

        logger.info(f"Rule '{new_rule}' added to firewall policy '{policy_name}'.")

    # def add_rule(self, security_group_name: str, rule) -> None:
    #     """Add single rule to existed Security Group."""
    #     # Get the existing firewall
    #     rule = compute_v1.Firewall.Allowed.from_dict(rule)
    #     firewall = self.get_security_group_by_name(security_group_name)
    #
    #     # Add the new rule
    #     firewall.allowed.append(rule)
    #
    #     # Update the firewall
    #     operation = self.firewall_client.update(
    #         project=self.credentials.project_id,
    #         firewall_resource=firewall,
    #     )
    #
    #     # Wait for the operation to complete
    #     self.wait_for_operation(name=operation.name)
    #
    #     logger.info(f"Rule '{rule}' added to security group '{security_group_name}'.")
