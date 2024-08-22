from typing import TYPE_CHECKING

from cloudshell.cp.core.flows.vm_details import AbstractVMDetailsFlow
if TYPE_CHECKING:
    from logging import Logger
    from cloudshell.cp.gcp.resource_conf import GCPResourceConfig


class GCPGetVMDetails(AbstractVMDetailsFlow):
    logger: Logger
    config: GCPResourceConfig

    def __attrs_pre_init__(self):
        super().__init__(self.logger)

    def _get_vm_details(self, deployed_app):
        """Get VM Details.

        :param deployed_app:
        :return:
        """
        sandbox_resource_group_name = self._reservation_info.get_resource_group_name()
        vm_resource_group_name = (
            deployed_app.resource_group_name or sandbox_resource_group_name
        )

        vm_actions = VMActions(azure_client=self._azure_client, logger=self._logger)
        vm_details_actions = VMDetailsActions(
            azure_client=self._azure_client, logger=self._logger
        )

        with self._cancellation_manager:
            vm = vm_actions.get_vm(
                vm_name=deployed_app.name, resource_group_name=vm_resource_group_name
            )

        if isinstance(deployed_app, AzureVMFromMarketplaceDeployedApp):
            return vm_details_actions.prepare_marketplace_vm_details(
                virtual_machine=vm, resource_group_name=vm_resource_group_name
            )

        return vm_details_actions.prepare_custom_vm_details(
            virtual_machine=vm, resource_group_name=vm_resource_group_name
        )
