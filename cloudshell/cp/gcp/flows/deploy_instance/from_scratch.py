from __future__ import annotations

from typing import TYPE_CHECKING

from attr import define, field

from cloudshell.cp.gcp.handlers.instance import Instance
from cloudshell.cp.gcp.flows.deploy_instance.base_flow import AbstractGCPDeployFlow

if TYPE_CHECKING:
    from cloudshell.cp.gcp.models.deploy_app import InstanceFromScratchDeployApp


@define
class GCPDeployInstanceFromScratchFlow(AbstractGCPDeployFlow):

    def _is_windows(self, deploy_app: InstanceFromScratchDeployApp) -> bool:
        return any(x for x in [deploy_app.disk_image, deploy_app.project_cloud] if "windows" in x)

    def _create_instance(
        self,
        deploy_app: InstanceFromScratchDeployApp,
        subnet_list: list[str]
    ) -> Instance:
        """Create Instance object based on provided attributes."""
        return Instance(
            deploy_app=deploy_app,
            resource_config=self.resource_config,
            subnet_list = subnet_list,
        ).from_scratch()
