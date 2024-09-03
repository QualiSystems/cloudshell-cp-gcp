from __future__ import annotations

import re

from attrs import define, field
from typing import TYPE_CHECKING

GCP_NAME_PATTERN = r"(?:[a-z](?:[-a-z0-9]{0,61}[a-z0-9])?)"
pattern_remove_symbols = re.compile(r"[^\w\d\-\.]")

if TYPE_CHECKING:
    pass


def generate_name(name: str) -> str:
    new_name = name.lower().replace("-", "--")
    new_name = pattern_remove_symbols.sub("", new_name)
    return re.sub(r"[^a-z0-9-]", "-", new_name)


def generate_vpc_name(name: str) -> str:
    return f"quali-{generate_name(name)}"

"""
reservationID = 2b70ac3b-aa35-4dda-b18b-f7d26235139a
CS_Subnet     = Subnet 10.10.0.0-10.10.10.0
"""
DEFAULT_NAME_PREFIX = "quali"
GOOGLE_NAME_MAX_LENGTH = 62


@define
class GCPNameGenerator:
    prefix: str = DEFAULT_NAME_PREFIX
    max_length: int = GOOGLE_NAME_MAX_LENGTH

    def __attrs_post_init__(self):
        self.prefix_length = len(self.prefix)
        self.max_core_length = self.max_length - self.prefix_length - 1

    def ssh_keys(self) -> str:
        """Hardcoded Name"""
        pass

    def subnet(self, cs_subnet: str) -> str:
        """quali-CS_Subnet"""
        pass

    def network(self, reservation_id: str) -> str:
        """quali-reservationID"""
        pass

    def instance(self, app_name: str, generate: bool = True) -> str:
        """1. verify app_name and set or raise 2. generate vm name based on app_name"""
        if generate:
            # generate instance name
            pass
        else:
            # verify app name only
            pass

    def vm_disk(self, instance_name: str, disk_num: int) -> str:
        """app_name-disk-1"""
        """
        app_name-disk-boot-0
        app_name-disk-data-1
        app_name-disk-data-2
        
        
        """
        pass

    def snapshot(self) -> str:
        """"""
        pass

    def firewall_rule(
            self,
            instance_name: str,
            dst: str,
            dst_port: int,
            protocol: str
    ) -> str:
        """quali-vm_name-dst-dst_port-protocol"""
        pass

    def firewall_policy(self, instance_name: str) -> str:
        """quali-vm_name"""
        pass

    def public_ip(self, instance_name: str) -> str:
        """quali-vm_name-public-ip"""
        pass

    def route(self, reservation_id: str, dst: str) -> str:
        """quali-reservationID-dst"""
        pass

    def image(self) -> str:
        """"""
        pass


"""

###########################################
ssh keys        -> hc-name
subnet          -> quali-CS_Subnet
network/vpc     -> quali-reservationID
app-appname     -> 1. verify app_name and set or raise 2. generate vm name based on app_name
vm disk         -> app_name+disk+disk_num
snapshots       -> take a look on existed implementation
Security Group Rule / NSG Rule / Firewall Rule   -> quali-vm_name-dst-dst_port-protocol
Security Group      / NSG      / Firewall Policy -> quali-vm_name
Public_IP       -> quali-vm_name-public-ip


Route -> quali-reservationID-dst
images gen?
IAM Role/Policy gen (2+ phase)
"""
