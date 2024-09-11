from __future__ import annotations

import logging
from abc import abstractmethod
from typing import TYPE_CHECKING

from cloudshell.cp.core.flows import AbstractDeployFlow
from cloudshell.cp.core.request_actions import DeployVMRequestActions
from cloudshell.cp.core.rollback import RollbackCommandsManager

from cloudshell.cp.gcp.handlers.vpc import VPCHandler
from cloudshell.cp.gcp.helpers.name_generator import GCPNameGenerator
from cloudshell.cp.gcp.actions.vm_details_actions import VMDetailsActions
from cloudshell.cp.gcp.flows.deploy_instance.commands import DeployInstanceCommand


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
        deployed_vm_id: int,
        deploy_app: BaseGCPDeployApp
    ) -> VmDetailsData:
        """Prepare CloudShell VM Details model."""
        vm_details_actions = VMDetailsActions(
            self.proxmox_api,
            self._resource_config,
            self._cancellation_manager,
        )
        return vm_details_actions.create(deployed_vm_id, deploy_app)

    def _prepare_deploy_app_result(
        self,
        deploy_app: BaseGCPDeployApp,
        instance_name: str,
    ) -> DeployAppResult:
        vm_details_data = self._prepare_vm_details_data(
            deployed_vm_id=deployed_vm_id,
            deploy_app=deploy_app,
        )

        logger.info(f"Prepared VM details: {vm_details_data}")

        return DeployAppResult(
            actionId=deploy_app.actionId,
            vmUuid=str(deployed_vm_id),
            vmName=instance_name,
            vmDetailsData=vm_details_data,
            deployedAppAdditionalData={
                "ip_regex": deploy_app.ip_regex,
                "refresh_ip_timeout": deploy_app.refresh_ip_timeout,
                "auto_power_off": deploy_app.auto_power_off,
                "auto_delete": deploy_app.auto_delete,
            },
            deployedAppAttributes=self._prepare_app_attrs(deploy_app, deployed_vm_id),
        )

    @abstractmethod
    def _create_instance(self, deploy_app: BaseGCPDeployApp, subnet_list: list[str]) \
            -> Instance:
        """"""
        pass

    def _deploy(self, request_actions: DeployVMRequestActions) -> DeployAppResult:
        """Deploy Proxmox Instance."""
        # noinspection PyTypeChecker

        deploy_app: BaseGCPDeployApp = request_actions.deploy_app
        subnet_list = [x.subnet_id for x in request_actions.connect_subnets]
        if not subnet_list:
            subnet_list = []

        with self.cancellation_manager:
            instance = self._create_instance(
                deploy_app=deploy_app,
                subnet_list=subnet_list
            )

        with self._rollback_manager:
            logger.info(f"Creating Instance {instance.name}")
            deployed_instance = DeployInstanceCommand(
                instance=instance,
                credentials=self.resource_config.credentials,
                rollback_manager=self._rollback_manager,
                cancellation_manager=self.cancellation_manager,
            ).execute()

        logger.info(f"Preparing Deploy App result for the {deployed_instance.name}")
        return self._prepare_deploy_app_result(
            deploy_app=deploy_app,
            instance_name=deployed_instance.name,
        )

    def _get_network(self) -> VPCHandler:
        """
        Get Network.
        """

        network_handler = VPCHandler.get_vpc_by_sandbox_id(self.resource_config.reservation_info.reservation_id)
        return network_handler.get_vpc_by_name(network_name)
