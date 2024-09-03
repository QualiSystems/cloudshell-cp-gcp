from __future__ import annotations

import logging
from contextlib import suppress
from functools import cached_property
from typing import TYPE_CHECKING

from google.api_core.exceptions import NotFound
from google.cloud import compute_v1
from google.cloud.compute_v1.types import Allowed, Denied

from cloudshell.cp.gcp.handlers.base import BaseGCPHandler

if TYPE_CHECKING:
    from google.cloud.compute_v1.types import Firewall

logger = logging.getLogger(__name__)


class FirewallRuleHandler(BaseGCPHandler):
    @cached_property
    def firewall_client(self):
        return compute_v1.FirewallsClient(credentials=self.credentials)

    def get_higher_priority(self, security_group_name: str) -> int:
        """Get the next available priority for the security group."""
        firewall = self.get_firewall_policy_by_name(security_group_name)
        priorities = [rule.priority for rule in firewall.allowed]
        return max(priorities) + 1 if priorities else 1000

    def get_lower_priority(self, security_group_name: str) -> int:
        """Get the next available priority for the security group."""
        firewall = self.get_firewall_policy_by_name(security_group_name)
        priorities = [rule.priority for rule in firewall.allowed]
        return min(priorities) - 1 if priorities else 1000

    # def create(
    #         self,
    #         firewall_policy_name: str,
    #         network_name: str,
    #         allow_policy_rules: list,
    #         deny_policy_rules: list,
    # ) -> Firewall:
    #     """"""
    #     # Define the firewall settings
    #     firewall = compute_v1.AddRuleRegionNetworkFirewallPolicyRequest()
    #     firewall.name = firewall_policy_name
    #     firewall.network = (
    #         f"projects/{self.credentials.project_id}/global/networks/{network_name}"
    #     )
    #     firewall.allowed = allow_policy_rules
    #     firewall.denied = deny_policy_rules
    #
    #     # Create the firewall
    #     operation = self.firewall_client.insert(
    #         project=self.credentials.project_id, firewall_resource=firewall
    #     )
    #
    #     # Wait for the operation to complete
    #     self.wait_for_operation(name=operation.name)
    #
    #     logger.info(f"Security group '{firewall_policy_name}' created successfully.")
    #     return self.get_firewall_policy_by_name(firewall_policy_name).name

    def get_firewall_rule_by_name(self, rule_name: str) -> (
            Firewall):
        """Get Security Group instance by its name."""
        logger.info("Getting security group")
        return self.firewall_client.get(
            project=self.credentials.project_id, firewall=rule_name
        )

    # def get_or_create_firewall_policy_by_name(
    #         self,
    #         firewall_policy_name: str,
    #         network: str,
    #         allow_policy_rules: list,
    #         deny_policy_rules: list
    # ) -> Firewall:
    #     """Get Security Group instance by its name."""
    #     logger.info("Getting security group")
    #     with suppress(NotFound):
    #         return self.firewall_client.get(
    #             project=self.credentials.project_id,
    #             firewall=firewall_policy_name,
    #         )
    #     return self.create(
    #         firewall_policy_name,
    #         network,
    #         allow_policy_rules,
    #         deny_policy_rules
    #     )

    def delete(self, rule_name: str) -> None:
        """Delete Security Group."""
        operation = self.firewall_client.delete(
            project=self.credentials.project_id, firewall=rule_name
        )
        operation.result()
        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name)

        logger.info(f"Security group '{rule_name}' deleted successfully.")

    def get_or_create_ingress_firewall_rule(
            self,
            rule_name: str,
            network_name: str,
            protocol: str,
            src_cidr: str,
            dst_cidr: str,
            ports: list[int] = None,
            allowed: bool = True,
            priority: int = None
    ):
        with suppress(NotFound):
            return self.get_firewall_rule_by_name(rule_name)
        return self.create_ingress_firewall_rule(
            rule_name,
            network_name,
            protocol,
            src_cidr,
            dst_cidr,
            ports,
            allowed,
            priority
        )

    def create_ingress_firewall_rule(
            self,
            rule_name: str,
            network_name: str,
            protocol: str,
            src_cidr: str,
            dst_cidr: str,
            ports: list[int] = None,
            allowed: bool = True,
            priority: int = None
    ):
        if not priority:
            priority = self.get_higher_priority(rule_name)

        if allowed:
            ports_rule = self.add_allowed_rule(protocol, ports)
            firewall_rule = compute_v1.Firewall(
                name=rule_name,
                network=f"projects/{self.credentials.project_id}"
                        f"/global/networks/{network_name}",
                direction="INGRESS",
                allowed=[ports_rule],
                source_ranges=[src_cidr],  # Specify source IP ranges
                destination_ranges=[dst_cidr],  # Specify destination IP ranges
                priority=priority,
            )
        else:
            ports_rule = self.add_deny_rule(protocol, ports)
            firewall_rule = compute_v1.Firewall(
                name=rule_name,
                network=f"projects/{self.credentials.project_id}"
                        f"/global/networks/{network_name}",
                direction="INGRESS",
                denied=[ports_rule],
                source_ranges=[src_cidr],  # Specify source IP ranges
                destination_ranges=[dst_cidr],  # Specify destination IP ranges
                priority=priority,
            )

        operation = self.firewall_client.insert(project=self.credentials.project_id,
                                                firewall_resource=firewall_rule)
        operation.result()  # Wait for the operation to complete

        print(f"Firewall rule '{rule_name}' created.")
        return firewall_rule

    def get_or_create_egress_firewall_rule(
            self,
            rule_name: str,
            network_name: str,
            protocol: str,
            src_cidr: str,
            dst_cidr: str,
            ports: list[int] = None,
            allowed: bool = True,
            priority: int = None
    ):
        rule = None
        with suppress(NotFound):
            rule = self.get_firewall_rule_by_name(rule_name)
        if not rule:
            return self.create_egress_firewall_rule(
                firewall_name=rule_name,
                network_name=network_name,
                protocol=protocol,
                src_cidr=src_cidr,
                dst_cidr=dst_cidr,
                ports=ports,
                priority=priority,
                allowed=allowed
            )

    def create_egress_firewall_rule(
            self,
            firewall_name: str,
            network_name: str,
            allowed: bool,
            protocol: str,
            src_cidr: str,
            ports: list[int],
            dst_cidr: str,
            priority: int = 1000
    ):
        if allowed:
            ports_rule = self.add_allowed_rule(protocol, ports)
        else:
            ports_rule = self.add_deny_rule(firewall_name, protocol, ports)

        firewall_rule = compute_v1.Firewall(
            name=firewall_name,
            network=f"projects/{self.credentials.project_id}"
                    f"/global/networks/{network_name}",
            direction="EGRESS",
            allowed=[ports_rule],
            source_ranges=[src_cidr],  # Specify source IP ranges
            destination_ranges=[dst_cidr],  # Specify destination IP ranges
            priority=priority,
        )

        operation = self.firewall_client.insert(project=self.credentials.project_id,
                                                firewall_resource=firewall_rule)
        operation.result()  # Wait for the operation to complete

        print(f"Firewall rule '{firewall_name}' created.")
        return firewall_rule

    def add_allowed_rule(self, protocol: str, ports: list[int]) -> \
            Allowed:
        """Add a new rule to an existing firewall policy."""
        new_rule = {
            "I_p_protocol": protocol,
        }
        if ports:
            new_rule["ports"] = list(map(str, ports))
        # Add the new rule
        return Allowed(**new_rule)

    def add_deny_rule(self, protocol: str, ports: list[int]) -> \
            Denied:
        """Add a new rule to an existing firewall policy."""
        # Get the existing firewall policy
        new_rule = {
            "I_p_protocol": protocol,
        }
        if ports:
            new_rule["ports"] = list(map(str, ports))

        # Add the new rule
        return Denied(**new_rule)

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
