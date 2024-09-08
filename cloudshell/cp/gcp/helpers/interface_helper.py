from __future__ import annotations
from typing import TYPE_CHECKING

from attr import define


if TYPE_CHECKING:
    from google.cloud.compute_v1.types import compute


@define
class InterfaceHelper:
    instance: compute.Instance

    def get_public_ip(self, if_index=0) -> str:
        network_interface = self.instance.network_interfaces[if_index]
        return network_interface.access_configs[0].nat_i_p if network_interface.access_configs else ""

    def get_private_ip(self, if_index=0) -> str:
        network_interface = self.instance.network_interfaces[if_index]
        return network_interface.network_i_p
