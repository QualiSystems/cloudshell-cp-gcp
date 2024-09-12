from __future__ import annotations

import json

from attr import define
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from cloudshell.cp.gcp.handlers.instance import InstanceHandler
    from cloudshell.cp.gcp.models.deployed_app import BaseGCPDeployApp
    from cloudshell.cp.gcp.resource_conf import GCPResourceConfig


@define
class GCPPowerFlow:
    deployed_app: BaseGCPDeployApp
    resource_config: GCPResourceConfig

    def _get_instance(self, instance_uuid) -> InstanceHandler:
        instance_data = json.loads(instance_uuid)
        instance_data["credentials"] = self.resource_config.credentials
        return InstanceHandler.get(**instance_data)

    def power_on(self):
        instance = self._get_instance(self.deployed_app.vmdetails.uid)
        if instance.status != "RUNNING":
            instance.start()

    def power_off(self):
        instance = self._get_instance(self.deployed_app.name)
        if instance.status not in ["STOPPING", "TERMINATED"]:
            instance.stop()
