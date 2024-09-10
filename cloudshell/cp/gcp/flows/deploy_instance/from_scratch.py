from __future__ import annotations

from typing import TYPE_CHECKING

from cloudshell.cp.gcp.handlers.instance import Instance
from cloudshell.cp.gcp.flows.deploy_instance.base_flow import AbstractGCPDeployFlow

if TYPE_CHECKING:
    from cloudshell.cp.gcp.models.deploy_app import InstanceFromScratchDeployApp


class GCPDeployInstanceFromScratchFlow(AbstractGCPDeployFlow):
    def _create_instance(
        self,
        deploy_app: InstanceFromScratchDeployApp,
    ) -> Instance:
        """Create Instance object based on provided attributes."""
        return Instance(
            deploy_app=deploy_app,
            resource_config=self.resource_config
        ).from_scratch()
