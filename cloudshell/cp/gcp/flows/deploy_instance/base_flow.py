from __future__ import annotations

import json
import logging
from abc import abstractmethod
from typing import TYPE_CHECKING

from cloudshell.cp.core.flows import AbstractDeployFlow
from cloudshell.cp.core.request_actions import DeployVMRequestActions
from cloudshell.cp.core.rollback import RollbackCommandsManager

from cloudshell.cp.gcp.helpers.constants import SET_WIN_PASSWORD_SCRIPT_TPL
from cloudshell.cp.gcp.actions.firewall_policy_actions import FirewallPolicyActions
from cloudshell.cp.gcp.handlers.ssh_keys import SSHKeysHandler
from cloudshell.cp.gcp.handlers.vpc import VPCHandler
from cloudshell.cp.gcp.helpers.interface_helper import InterfaceHelper
from cloudshell.cp.gcp.helpers.name_generator import GCPNameGenerator
from cloudshell.cp.gcp.actions.vm_details_actions import VMDetailsActions
from cloudshell.cp.gcp.flows.deploy_instance.commands import DeployInstanceCommand
from cloudshell.cp.gcp.helpers.network_tag_helper import get_network_tags, InboundPort

if TYPE_CHECKING:
    from cloudshell.cp.gcp.handlers.instance import Instance, InstanceHandler
    from cloudshell.cp.gcp.models.deploy_app import BaseGCPDeployApp
    from cloudshell.cp.gcp.resource_conf import GCPResourceConfig
    from cloudshell.api.cloudshell_api import CloudShellAPISession, ReservationInfo
    from cloudshell.cp.core.cancellation_manager import CancellationContextManager
    from cloudshell.cp.core.request_actions.models import (
        DeployAppResult,
        VmDetailsData,
    )

logger = logging.getLogger(__name__)


class AbstractGCPDeployFlow(AbstractDeployFlow):
    instance_handler: InstanceHandler
    resource_config: GCPResourceConfig
    cs_api: CloudShellAPISession
    # reservation_info: ReservationInfo
    cancellation_manager: CancellationContextManager

    def __attrs_post_init__(self):
        super().__init__(logger)
        self._rollback_manager = RollbackCommandsManager(logger)
        self.name_generator = GCPNameGenerator()

    def _prepare_vm_details_data(
        self,
        deployed_vm: InstanceHandler,
    ) -> VmDetailsData:
        """Prepare CloudShell VM Details model."""
        vm_details_actions = VMDetailsActions(
            config=self._resource_config,
            logger=self._logger,
        )
        return vm_details_actions.prepare_vm_details(deployed_vm)

    def _prepare_deploy_app_result(
        self,
        deploy_app: BaseGCPDeployApp,
        instance_handler: InstanceHandler,
        password: str = None,
    ) -> DeployAppResult:
        vm_details_data = self._prepare_vm_details_data(
            deployed_vm=instance_handler,
        )

        logger.info(f"Prepared VM details: {vm_details_data}")

        return DeployAppResult(
            actionId=deploy_app.actionId,
            vmUuid=json.dumps(
                {
                    "instance_name": instance_handler.instance.name,
                    "zone": instance_handler.instance.zone
                }
            ),
            vmName=instance_handler.instance.name,
            vmDetailsData=vm_details_data,
            deployedAppAdditionalData={
                "ip_regex": deploy_app.ip_regex,
                "refresh_ip_timeout": deploy_app.refresh_ip_timeout,
                "auto_power_off": deploy_app.auto_power_off,
                "auto_delete": deploy_app.auto_delete,
            },
            deployedAppAttributes=self._prepare_app_attrs(
                deploy_app,
                instance_handler,
                password
            ),
        )

    @abstractmethod
    def _create_instance(self, deploy_app: BaseGCPDeployApp, subnet_list: list[str]) \
            -> Instance:
        """"""
        pass

    @abstractmethod
    def _is_windows(self, deploy_app: BaseGCPDeployApp) -> bool:
        """"""
        pass

    def _deploy(self, request_actions: DeployVMRequestActions) -> DeployAppResult:
        """Deploy Proxmox Instance."""
        # noinspection PyTypeChecker
        network_handler = self._get_network()
        deploy_app: BaseGCPDeployApp = request_actions.deploy_app
        subnet_list = [x.subnet_id for x in request_actions.connect_subnets]
        if not subnet_list:
            subnet_list = network_handler.get_subnets()

        with self.cancellation_manager:
            instance = self._create_instance(
                deploy_app=deploy_app,
                subnet_list=subnet_list
            )

        net_tags = self._get_network_tags(instance, deploy_app)
        if net_tags:
            instance.tags = net_tags.keys()

        if self._is_windows(deploy_app) and deploy_app.password:
            instance.metadata["sysprep-specialize-script-ps1"] = \
                (
                    SET_WIN_PASSWORD_SCRIPT_TPL.format(
                        password=deploy_app.password,
                        user=deploy_app.user
                    )
                )

        with self._rollback_manager:
            logger.info(f"Creating Instance {instance.name}")
            deployed_instance = DeployInstanceCommand(
                instance=instance,
                credentials=self.resource_config.credentials,
                rollback_manager=self._rollback_manager,
                cancellation_manager=self.cancellation_manager,
            ).execute()

        logger.info(f"Instance {deployed_instance.name} created")

        firewall_actions = FirewallPolicyActions(
            credentials=self.resource_config.credentials
        )
        for tag_name, inbound_port in net_tags.items():
            firewall_actions.create_inbound_port_rule(
                network_name=network_handler.network.name,
                network_tag=tag_name,
                inbound_port=inbound_port,
            )

        logger.info(f"Preparing Deploy App result for the {deployed_instance.name}")
        return self._prepare_deploy_app_result(
            deploy_app=deploy_app,
            instance_handler=deployed_instance,
            password=deploy_app.password,
        )

    def _prepare_app_attrs(
            self,
            deploy_app: BaseGCPDeployApp,
            instance_handler: InstanceHandler,
            password: str = None,
    ) -> list[Attribute]:
        deployed_app_attrs = [
            Attribute("User", deploy_app.user),
            Attribute("Public IP", InterfaceHelper.get_public_ip(instance_handler)),
        ]
        if password:
            deployed_app_attrs.append(Attribute("Password", password))

        return deployed_app_attrs

    def _get_network(self) -> VPCHandler:
        """
        Get Network.
        """

        return VPCHandler.get_vpc_by_sandbox_id(
            self.resource_config.reservation_info.reservation_id,
            self.resource_config.credentials
        )

    def _get_tags(self, deploy_app: BaseGCPDeployApp) -> dict[str, str]:
        tags = self.resource_config.custom_tags | deploy_app.custom_tags
        tags["ssh-keys"] = self._add_ssh_key(deploy_app)

    def _get_network_tags(
            self,
            instance: Instance,
            deploy_app: BaseGCPDeployApp
    ) -> dict[str, InboundPort]:
        net_tags = get_network_tags(instance.name,
                                    deploy_app.inbound_ports)
        return net_tags

    def _add_ssh_key(self, deploy_app: BaseGCPDeployApp) -> str:
        ssh_key_handler = SSHKeysHandler(self.resource_config.credentials)
        key = ssh_key_handler.download_ssh_key(
            self.resource_config.keypairs_location,
            file_path=f"{self.resource_config.reservation_info.reservation_id}/public_key"
        )
        return f"{deploy_app.user}: {key}"

