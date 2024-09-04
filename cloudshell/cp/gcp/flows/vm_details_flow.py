from __future__ import annotations

from typing import TYPE_CHECKING

from attr import define
from cloudshell.cp.core.flows.vm_details import AbstractVMDetailsFlow

from cloudshell.cp.gcp.actions.vm_details_actions import VMDetailsActions
from cloudshell.cp.gcp.handlers.instance import InstanceHandler
from cloudshell.cp.gcp.models.deployed_app import BaseGCPDeployApp

if TYPE_CHECKING:
    from logging import Logger
    from cloudshell.cp.gcp.resource_conf import GCPResourceConfig


@define
class GCPGetVMDetailsFlow(AbstractVMDetailsFlow):
    logger: Logger
    config: GCPResourceConfig

    def _get_vm_details(self, deployed_app):
        """Get VM Details.

        :param deployed_app:
        :return:
        """
        sandbox_id = self.config.reservation_info.reservation_id

        vm_actions = InstanceHandler(azure_client=self._azure_client, logger=self._logger)
        vm_details_actions = VMDetailsActions(
            config=self.config, logger=self._logger
        )

        # with self._cancellation_manager:
        vm = vm_actions.get_vm_by_name(
            vm_name=deployed_app.name,
        )

        if isinstance(deployed_app, BaseGCPDeployApp):
            return vm_details_actions.prepare_marketplace_vm_details(
                virtual_machine=vm, resource_group_name=vm_resource_group_name
            )

        return vm_details_actions.prepare_custom_vm_details(
            virtual_machine=vm, resource_group_name=vm_resource_group_name
        )
