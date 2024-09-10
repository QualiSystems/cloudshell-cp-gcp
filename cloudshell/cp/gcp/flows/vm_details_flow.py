from __future__ import annotations

import json
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

    def __attrs_post_init__(self):
        super().__init__(self.logger)

    def _get_vm_details(self, deployed_app: BaseGCPDeployApp):
        """Get VM Details.

        :param deployed_app:
        :return:
        """
        name, zone = json.loads(deployed_app.vmdetails.uid).values()

        instance_handler = InstanceHandler.get(
            instance_name=name,
            credentials=self.config.credentials,
            zone=zone,
        )
        vm_details_actions = VMDetailsActions(
            config=self.config, logger=self.logger
        )

        return vm_details_actions.prepare_vm_details(
            instance_handler=instance_handler
        )
