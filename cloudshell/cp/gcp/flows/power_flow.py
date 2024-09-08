from __future__ import annotations

from attr import define

from cloudshell.cp.gcp.handlers.instance import InstanceHandler
from cloudshell.cp.gcp.models.deployed_app import BaseGCPDeployApp
from cloudshell.cp.gcp.resource_conf import GCPResourceConfig


@define
class GCPPowerFlow:
    deployed_app: BaseGCPDeployApp
    resource_config: GCPResourceConfig

    def _get_instance(self, instance_name) -> InstanceHandler:
        return InstanceHandler.get_vm_by_name(instance_name)

    def power_on(self):
        instance = self._get_instance(self.deployed_app.name)
        if instance.status != "RUNNING":
            instance.start()

    def power_off(self):
        instance = self._get_instance(self.deployed_app.name)
        if instance.status not in ["STOPPING", "TERMINATED"]:
            instance.stop()
