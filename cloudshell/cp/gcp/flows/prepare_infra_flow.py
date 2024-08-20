from __future__ import annotations

from attrs import define, field
from typing import TYPE_CHECKING

from cloudshell.cp.core.flows.prepare_sandbox_infra import (
    AbstractPrepareSandboxInfraFlow,
)

from cloudshell.cp.core.utils import generate_ssh_key_pair
from cloudshell.cp.gcp.handlers.ssh_keys import SSHKeysHandler
from cloudshell.cp.gcp.handlers.subnet import SubnetHandler
from cloudshell.cp.gcp.handlers.vpc import VPCHandler
from cloudshell.cp.gcp.helpers.name_generator import generate_name, generate_vpc_name


if TYPE_CHECKING:
    from logging import Logger
    from cloudshell.cp.core.reservation_info import ReservationInfo
    from cloudshell.cp.core.request_actions import (
        PrepareSandboxInfraRequestActions as RequestActions,
    )
    from cloudshell.cp.gcp.resource_conf import GCPResourceConfig


@define
class PrepareGCPInfraFlow(AbstractPrepareSandboxInfraFlow):
    logger: Logger
    config: GCPResourceConfig
    reservation_info: ReservationInfo
    vpc: str = field(init=False, default=None)

    def __attrs_pre_init__(self):
        super().__init__(self.logger)

    def prepare_common_objects(self, request_actions: RequestActions) -> None:
        """"""
        vpc_handler = VPCHandler(self.config.credentials)
        self.vpc = vpc_handler.get_or_create_vpc(
            generate_vpc_name(self.reservation_info.reservation_id)
        )

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
                        subnet_name=generate_name(subnet_request.get_alias())
                    )
                }
            )
        return subnet_results

    def create_ssh_keys(self, request_actions: RequestActions) -> str:
        """Create SSH Keys."""
        ssh_keys_handler = SSHKeysHandler(self.config.credentials)
        private_key, public_key = ssh_keys_handler.get_ssh_key_pair(
            bucket_name=self.config.keypairs_location,
            folder_path=self.reservation_info.reservation_id,
        )
        if not private_key or not public_key:
            private_key, public_key = generate_ssh_key_pair()
            ssh_keys_handler.upload_ssh_keys(
                bucket_name=self.config.keypairs_location,
                folder_path=self.reservation_info.reservation_id,
                private_key=private_key,
                public_key=public_key,
            )
        return private_key
