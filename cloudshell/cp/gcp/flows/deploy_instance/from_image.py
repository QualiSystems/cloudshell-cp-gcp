from __future__ import annotations

from typing import TYPE_CHECKING

from cloudshell.cp.gcp.handlers.instance import Instance
from cloudshell.cp.gcp.flows.deploy_instance.base_flow import AbstractGCPDeployFlow

if TYPE_CHECKING:
    from cloudshell.cp.gcp.models.deploy_app import InstanceFromMachineImageDeployApp


class GCPDeployInstanceFromImageFlow(AbstractGCPDeployFlow):

    def _is_windows(self, deploy_app: InstanceFromMachineImageDeployApp) -> bool:
        return any(x for x in [deploy_app.machine_image] if "windows" in x)

    def _create_instance(
        self,
        deploy_app: InstanceFromMachineImageDeployApp,
        subnet_list: list[str],
    ) -> Instance:
        """Create Instance object based on Machine Image."""
        return Instance(
            deploy_app=deploy_app,
            resource_config=self.resource_config,
            subnet_list=subnet_list,
        ).from_machine_image()
