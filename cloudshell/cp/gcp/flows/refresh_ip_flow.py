from __future__ import annotations

import json

from attr import define
from typing_extensions import TYPE_CHECKING

from cloudshell.cp.gcp.handlers.instance import InstanceHandler
from cloudshell.cp.gcp.helpers.interface_helper import InterfaceHelper


if TYPE_CHECKING:
    from logging import Logger
    from cloudshell.cp.gcp.models.deployed_app import BaseGCPDeployApp
    from cloudshell.cp.core.request_actions import (
        PrepareSandboxInfraRequestActions as RequestActions,
    )
    from cloudshell.cp.core.cancellation_manager import CancellationContextManager
    from cloudshell.cp.gcp.resource_conf import GCPResourceConfig
    from google.cloud.compute_v1.types import compute


@define
class GCPRefreshIPFlow:
    _deployed_app: BaseGCPDeployApp
    _resource_config: GCPResourceConfig
    _cancellation_manager: CancellationContextManager

    def _get_instance(self, instance_uuid) -> compute.Instance:
        instance_data = json.loads(instance_uuid)
        instance_data["credentials"] = self._resource_config.credentials
        return InstanceHandler.get(**instance_data).instance

    def refresh_ip(self) -> str:
        internal_ip = ""
        try:
            instance_name = self._deployed_app.vmdetails.uid
            instance = self._get_instance(instance_name)
            if instance.status != "RUNNING":
                raise Exception(f"Instance {instance_name} is not running")
            network_interface = InterfaceHelper(instance)

            # Get the internal and external IP addresses
            internal_ip = network_interface.get_private_ip()
            external_ip = network_interface.get_public_ip()
            if not internal_ip:
                raise Exception("Internal IP address not found")
            self._deployed_app.update_private_ip(self._deployed_app.name, internal_ip)
            if external_ip:
                self._deployed_app.update_public_ip(
                    external_ip
                )
        except Exception:
            if self._deployed_app.wait_for_ip:
                raise
        return internal_ip
