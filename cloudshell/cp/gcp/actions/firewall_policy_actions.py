from __future__ import annotations

import logging
from functools import cached_property
from logging import Logger

from attr import define
from typing_extensions import TYPE_CHECKING

from cloudshell.cp.gcp.handlers.firewall_rule import FirewallRuleHandler
from cloudshell.cp.gcp.resource_conf import GCPResourceConfig

if TYPE_CHECKING:
    from google.auth.credentials import Credentials


logger = logging.getLogger(__name__)


@define
class FirewallPolicyActions:
    NSG_RULE_NAME_TPL = "allow-sandbox-traffic-to-{subnet_cidr}"
    NSG_DENY_RULE_NAME_TPL = "deny-traffic-from-other-sandboxes"
    NSG_DENY_PRV_RULE_PRIORITY = 2000
    NSG_DENY_PRV_RULE_NAME_TPL = "deny_internet_traffic_to_priv_subnet_{subnet_cidr}"
    VM_NSG_NAME_TPL = "rule_{vm_name}"
    INBOUND_RULE_DIRECTION = "inbound"

    NSG_ADD_MGMT_RULE_PRIORITY = 4000
    NSG_ADD_MGMT_RULE_NAME_TPL = "allow-{mgmt_network}-to-{sandbox_cidr}"
    NSG_DENY_OTHER_SB_RULE_PRIORITY = 4090

    credentials: Credentials
    _lower_priority: int = NSG_DENY_PRV_RULE_PRIORITY
    _higher_priority: int = NSG_ADD_MGMT_RULE_PRIORITY

    @cached_property
    def fr_handler(self):
        return FirewallRuleHandler(credentials)

    def create_firewall_rules(self, request_actions, network_name,
                              additional_mgmt_networks=None):
        """Create all required Firewalls rules.

        :return:
        """
        # with self._cancellation_manager:

        self._create_nsg_allow_sandbox_traffic_to_subnet_rules(
            request_actions=request_actions,
            network_name=network_name,
        )

        self._create_nsg_deny_access_to_private_subnet_rules(
            request_actions=request_actions,
            network_name=network_name,
        )

        self._create_nsg_deny_traffic_from_other_sandboxes_rule(
            request_actions=request_actions,
            network_name=network_name,
        )

    def _create_nsg_allow_sandbox_traffic_to_subnet_rules(
            self,
            request_actions,
            network_name
    ):
        """Create NSG allow Sandbox traffic to subnet rules.

        :param request_actions:
        :param str nsg_name:
        :param str resource_group_name:
        :return:
        """
        result = []
        for action in request_actions.prepare_subnets:
            self._lower_priority += 1
            self._lower_priority = self.fr_handler.get_or_create_ingress_firewall_rule(
                rule_name=self.NSG_RULE_NAME_TPL.format(
                    subnet_cidr=action.get_cidr().replace("/", "--").replace(".", "-")
                ),
                network_name=network_name,
                src_cidr=request_actions.sandbox_cidr,
                dst_cidr=action.get_cidr(),
                protocol="all",
                priority=self._lower_priority,
            )

        return result

    def _create_nsg_deny_access_to_private_subnet_rules(
            self,
            request_actions,
            network_name
    ):
        """Create NSG deny access to private subnet rules.

        :param request_actions:
        :param str nsg_name:
        :param str resource_group_name:
        :return:
        """
        for action in request_actions.prepare_private_subnets:
            self._lower_priority += 1
            subnet_cidr = action.get_cidr()
            self._lower_priority = self.fr_handler.get_or_create_ingress_firewall_rule(
                rule_name=self.NSG_DENY_PRV_RULE_NAME_TPL.format(
                    subnet_cidr=subnet_cidr
                ).replace("/", "--").replace(".", "-"),
                protocol="all",
                network_name=network_name,
                src_cidr=request_actions.sapndbox_cidr,
                dst_cidr=subnet_cidr,
                allowed=False,
                priority=self._lower_priority,
            )

    def _create_nsg_additional_mgmt_networks_rules(
            self,
            request_actions,
            network_name,
            additional_mgmt_networks
    ):
        """Create NSG rules for the additional MGMT networks.

        :param request_actions:
        :param str nsg_name:
        :param str resource_group_name:
        :return:
        """
        for mgmt_network in additional_mgmt_networks:
            self._higher_priority += 1
            self._higher_priority = self.fr_handler.get_or_create_ingress_firewall_rule(
                rule_name=self.NSG_ADD_MGMT_RULE_NAME_TPL.format(
                    mgmt_network=mgmt_network, sandbox_cidr=request_actions.sandbox_cidr
                ).replace("/", "--").replace(".", "-"),
                network_name=network_name,
                protocol="all",
                src_cidr=mgmt_network,
                dst_cidr=request_actions.sandbox_cidr,
                priority=self._higher_priority
            )

    def _create_nsg_deny_traffic_from_other_sandboxes_rule(
        self,
        request_actions,
        network_name
    ):
        """Create NSG deny traffic from other sandboxes rule.

        :param request_actions:
        :param str nsg_name:
        :param str resource_group_name:
        :return:
        """
        return self.fr_handler.get_or_create_ingress_firewall_rule(
            rule_name=self.NSG_DENY_RULE_NAME_TPL,
            network_name=network_name,
            src_cidr="0.0.0.0/0",
            dst_cidr=request_actions.sandbox_cidr,
            allowed=False,
            protocol="all",
            priority=self.NSG_DENY_OTHER_SB_RULE_PRIORITY,
        )

    def create_inbound_port_rule(
            self,
            network_name: str,
            rule_name: str,
            network_tag: str,
            src_address: str,
            port_range: list[str],
            protocol: str = "tcp"
    ):
        """Create inbound port rule.

        """
        priority = self.fr_handler.get_higher_priority(network_name=network_name)
        return self.fr_handler.get_or_create_ingress_firewall_rule(
            rule_name=rule_name,
            network_name=network_name,
            src_cidr=src_address,
            ports=port_range,
            allowed=True,
            protocol=protocol,
            priority=priority,
            network_tag=network_tag,
        )
