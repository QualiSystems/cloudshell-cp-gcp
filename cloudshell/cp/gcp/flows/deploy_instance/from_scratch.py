from __future__ import annotations

from typing import TYPE_CHECKING

from cloudshell.cp.gcp.handlers.instance import Instance, InstanceHandler
from cloudshell.cp.gcp.flows.deploy_instance.base_flow import AbstractGCPDeployFlow

if TYPE_CHECKING:
    from cloudshell.cp.gcp.models.deploy_app import InstanceFromScratchDeployApp


@define
class GCPDeployInstanceFromScratchFlow(AbstractGCPDeployFlow):
    password: field(str, default=None)

    def _create_instance(
        self,
        deploy_app: InstanceFromScratchDeployApp,
            subnet_list: list[str]
    ) -> Instance:
        """Create Instance object based on provided attributes."""
        instance = Instance(
            deploy_app=deploy_app,
            resource_config=self.resource_config,
        subnet_list = subnet_list,
        ).from_scratch()
