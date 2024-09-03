from functools import cached_property
from typing import List

from cloudshell.cp.gcp.handlers.firewall_policy import FirewallPolicyHandler
from cloudshell.cp.gcp.handlers.firewall_rule import FirewallRuleHandler


class FirewallPolicyActions:
    NSG_RULE_NAME_TPL = "allow-sandbox-traffic-to-{subnet_cidr}"
    NSG_DENY_RULE_NAME_TPL = "deny-traffic-from-other-sandboxes"
    NSG_DENY_PRV_RULE_PRIORITY = 2000
    NSG_DENY_PRV_RULE_NAME_TPL = "deny_internet_traffic_to_priv_subnet_{subnet_cidr}"
    VM_NSG_NAME_TPL = "rule_{vm_name}"
    INBOUND_RULE_DIRECTION = "inbound"
    CUSTOM_NSG_RULE_NAME_TPL = (
        "rule-{vm_name}-{dst_address}-"
        "{dst_port_range}-{protocol}"
    )
    NSG_ADD_MGMT_RULE_PRIORITY = 4000
    NSG_ADD_MGMT_RULE_NAME_TPL = "allow-{mgmt_network}-to-{sandbox_cidr}"
    NSG_DENY_OTHER_SB_RULE_PRIORITY = 4090

    def __init__(
        self,
        resource_config,
        firewall_policy_name,
        reservation_info,
        logger,
    ):
        """Init command.

        :param resource_config:
        :param reservation_info:
        :param cancellation_manager:
        :param logger:
        """
        self.logger = logger
        self.config = resource_config
        self.firewall_policy_name = firewall_policy_name
        self._reservation_info = reservation_info
        self._2k_priority = self.NSG_DENY_PRV_RULE_PRIORITY
        self._4k_priority = self.NSG_ADD_MGMT_RULE_PRIORITY
        # self._cancellation_manager = cancellation_manager
        # self._rollback_manager = RollbackCommandsManager(logger=self._logger)
        # self._tags_manager = AzureTagsManager(
        #     reservation_info=self._reservation_info, resource_config=resource_config
        # )

    @cached_property
    def fr_handler(self):
        return FirewallRuleHandler(self.config.credentials)

    @cached_property
    def fp_handler(self):
        return FirewallPolicyHandler(self.config.credentials)

    def create_firewall_rules(self, request_actions, network_name):
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

        # self._create_nsg_additional_mgmt_networks_rules(
        #     request_actions=request_actions,
        #     network_name=network_name,
        # )

        # self._create_nsg_allow_mgmt_vnet_rule(
        #     request_actions=request_actions,
        #     nsg_name=nsg_name,
        #     resource_group_name=resource_group_name,
        # )

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
            self._2k_priority += 1
            self._2k_priority = self.fr_handler.get_or_create_ingress_firewall_rule(
                rule_name=self.NSG_RULE_NAME_TPL.format(
                    subnet_cidr=action.get_cidr().replace("/", "--").replace(".", "-")
                ),
                network_name=network_name,
                src_cidr=request_actions.sandbox_cidr,
                dst_cidr=action.get_cidr(),
                protocol="all",
                priority=self._2k_priority,
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
            self._2k_priority += 1
            subnet_cidr = action.get_cidr()
            self._2k_priority = self.fr_handler.get_or_create_ingress_firewall_rule(
                rule_name=self.NSG_DENY_PRV_RULE_NAME_TPL.format(
                    subnet_cidr=subnet_cidr
                ).replace("/", "--").replace(".", "-"),
                protocol="all",
                network_name=network_name,
                src_cidr=request_actions.sapndbox_cidr,
                dst_cidr=subnet_cidr,
                allowed=False,
                priority=self._2k_priority,
            )

    def _create_nsg_additional_mgmt_networks_rules(
            self,
            request_actions,
            network_name
    ):
        """Create NSG rules for the additional MGMT networks.

        :param request_actions:
        :param str nsg_name:
        :param str resource_group_name:
        :return:
        """
        for mgmt_network in self.config.additional_mgmt_networks:
            self._4k_priority += 1
            self._4k_priority = self.fr_handler.get_or_create_ingress_firewall_rule(
                rule_name=self.NSG_ADD_MGMT_RULE_NAME_TPL.format(
                    mgmt_network=mgmt_network, sandbox_cidr=request_actions.sandbox_cidr
                ).replace("/", "--").replace(".", "-"),
                network_name=network_name,
                protocol="all",
                src_cidr=mgmt_network,
                dst_cidr=request_actions.sandbox_cidr,
                priority=self._4k_priority
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
            vm_name: str,
            network_tag: str,
            src_address: str,
            port_range: list[str],
            protocol: str = "tcp"
    ):
        """Create inbound port rule.

        """
        ports_name = "-".join(
            map(lambda x: str(x).replace("-", "--"), port_range)
        )
        priority = self.fr_handler.get_higher_priority(network_name=network_name)
        return self.fr_handler.get_or_create_ingress_firewall_rule(
            rule_name=self.CUSTOM_NSG_RULE_NAME_TPL.format(
                vm_name=vm_name,
                dst_address=src_address.replace(
                    "/", "--"
                ).replace(
                    ".", "-"
                ),
                dst_port_range=ports_name,
                protocol=protocol,
            ),
            network_name=self.config.network_name,
            src_cidr=src_address,
            ports=port_range,
            allowed=True,
            protocol=protocol,
            priority=priority,
            network_tag=network_tag,
        )

    # def _create_nsg_allow_mgmt_vnet_rule(
    #     self, request_actions, nsg_name, resource_group_name, rules_priority_generator
    # ):
    #     """Create NSG allow MGMT vNET rule.
    #
    #     :param request_actions:
    #     :param str nsg_name:
    #     :param str resource_group_name:
    #     :return:
    #     """
    #     nsg_actions = NetworkSecurityGroupActions(
    #         azure_client=self._azure_client, logger=self._logger
    #     )
    #     network_actions = NetworkActions(
    #         azure_client=self._azure_client, logger=self._logger
    #     )
    #
    #     if network_actions.mgmt_virtual_network_exists(
    #         self.config.management_group_name
    #     ):
    #         commands.CreateAllowMGMTVnetRuleCommand(
    #             rollback_manager=self._rollback_manager,
    #             cancellation_manager=self._cancellation_manager,
    #             mgmt_resource_group_name=self.config.management_group_name,
    #             resource_group_name=resource_group_name,
    #             network_actions=network_actions,
    #             nsg_actions=nsg_actions,
    #             nsg_name=nsg_name,
    #             sandbox_cidr=request_actions.sandbox_cidr,
    #             rules_priority_generator=rules_priority_generator,
    #         ).execute()
