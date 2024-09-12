from __future__ import annotations

from attrs import define, field
from typing import TYPE_CHECKING

from cloudshell.cp.core.flows.prepare_sandbox_infra import (
    AbstractPrepareSandboxInfraFlow,
)

from cloudshell.cp.core.utils import generate_ssh_key_pair

from cloudshell.cp.gcp.actions.firewall_policy_actions import FirewallPolicyActions
from cloudshell.cp.gcp.handlers.ssh_keys import SSHKeysHandler
from cloudshell.cp.gcp.handlers.subnet import SubnetHandler
from cloudshell.cp.gcp.handlers.vpc import VPCHandler
from cloudshell.cp.gcp.helpers.name_generator import GCPNameGenerator

if TYPE_CHECKING:
    from logging import Logger
    from cloudshell.cp.core.request_actions import (
        PrepareSandboxInfraRequestActions as RequestActions,
    )
    from cloudshell.cp.gcp.resource_conf import GCPResourceConfig


@define
class PrepareGCPInfraFlow(AbstractPrepareSandboxInfraFlow):
    logger: Logger
    config: GCPResourceConfig
    vpc: str = field(init=False, default=None)
    name_generator: GCPNameGenerator = field(init=False, default=GCPNameGenerator())

    def __attrs_post_init__(self):
        super().__init__(self.logger)

    def prepare_common_objects(self, request_actions: RequestActions) -> None:
        """"""
        vpc_handler = VPCHandler(self.config.credentials)
        self.vpc = vpc_handler.get_or_create_vpc(
            self.name_generator.network(
                self.config.reservation_info.reservation_id)
        )
        self._create_firewall_rules(request_actions, self.vpc)

    def prepare_cloud_infra(self, request_actions: RequestActions) -> str:
        """Create vpc using vpc handler."""
        return self.vpc

    def prepare_subnets(self, request_actions: RequestActions) -> dict[str, str]:
        """Create subnets using subnet handler."""
        subnet_results = {}
        subnet_handler = SubnetHandler(self.config.credentials, self.config.region)
        for subnet_request in request_actions.prepare_subnets:
            subnet_results.update(
                {
                    subnet_request.actionId: subnet_handler.get_or_create_subnet(
                        network_name=self.vpc,
                        ip_cidr_range=subnet_request.get_cidr(),
                        subnet_name=self.name_generator.subnet(
                            subnet_request.get_alias()
                        ),
                    )
                }
            )
        return subnet_results

    def create_ssh_keys(self, request_actions: RequestActions) -> str:
        """Create SSH Keys."""
        ssh_keys_handler = SSHKeysHandler(self.config.credentials)
        private_key, public_key = ssh_keys_handler.get_ssh_key_pair(
            bucket_name=self.config.keypairs_location,
            folder_path=self.config.reservation_info.reservation_id,
        )
        if not private_key or not public_key:
            private_key, public_key = generate_ssh_key_pair()
            ssh_keys_handler.upload_ssh_keys(
                bucket_name=self.config.keypairs_location,
                folder_path=self.config.reservation_info.reservation_id,
                private_key=private_key,
                public_key=public_key,
            )
        return private_key

    def _create_firewall_rules(self, request_actions, network_name):
        """Create all required NSG rules.

        :param request_actions:
        :return:
        """
        fp_actions = FirewallPolicyActions(
            credentials=self.config.credentials,
            # firewall_policy_name=f"quali-"
            #                      f"{self.config.reservation_info.reservation_id}",
            # reservation_info=self.config.reservation_info,
            # cancellation_manager=None,
        )
        fp_actions.create_firewall_rules(request_actions, network_name)
