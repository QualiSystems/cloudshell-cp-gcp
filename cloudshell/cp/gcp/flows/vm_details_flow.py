from __future__ import annotations

from typing import TYPE_CHECKING

from attr import define
from cloudshell.cp.core.flows.vm_details import AbstractVMDetailsFlow

from cloudshell.cp.gcp.actions.vm_details_actions import VMDetailsActions
from cloudshell.cp.gcp.handlers.instance import InstanceHandler

if TYPE_CHECKING:
    from logging import Logger
    from cloudshell.cp.gcp.resource_conf import GCPResourceConfig
    from cloudshell.cp.gcp.models.deployed_app import BaseGCPDeployApp


@define
class GCPGetVMDetailsFlow(AbstractVMDetailsFlow):
    logger: Logger
    config: GCPResourceConfig

    def _get_vm_details(self, deployed_app: BaseGCPDeployApp):
        """Get VM Details.

        :param deployed_app:
        :return:
        """
        # sandbox_id = self.config.reservation_info.reservation_id

        vm_actions = InstanceHandler()
        vm_details_actions = VMDetailsActions(
            config=self.config, logger=self._logger
        )

        # with self._cancellation_manager:
        vm = vm_actions.get_vm_by_name(
            vm_name=deployed_app.name,
        )

        return vm_details_actions.prepare_custom_vm_details(instance=vm)
