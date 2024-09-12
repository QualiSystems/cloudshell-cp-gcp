from __future__ import annotations

import re
from attrs import define, field

from cloudshell.cp.core.utils.name_generator import generate_short_unique_string
from cloudshell.cp.gcp.helpers.errors import AttributeGCPError

CS_ALLOWED_SYMBOLS = " -.|_[]"
GCP_NAME_PREFIX = "quali"
GCP_NAME_MAX_LENGTH = 62


@define
class GCPNameGenerator:
    prefix: str = GCP_NAME_PREFIX
    max_length: int = GCP_NAME_MAX_LENGTH
    prefix_length: int = field(init=False)
    max_core_length: int = field(init=False)
    GCP_NAME_PATTERN: int = field(init=False, default=r"")

    def __attrs_post_init__(self):
        self.prefix_length = len(self.prefix)
        self.max_core_length = self.max_length - self.prefix_length - 1
        self.GCP_NAME_PATTERN = rf"^(?:[a-z](?:[-a-z0-9]{{0,{self.max_length-1}}}[a-z0-9]))$"

    def validator(func):
        def wrapper(self, *args, **kwargs):
            name = func(self, *args, **kwargs)
            if not re.match(pattern=self.GCP_NAME_PATTERN, string=name):
                raise AttributeGCPError(
                    f"Name '{name}' doesn't match GCP Name Pattern."
                )
            return name
        return wrapper

    @validator
    def ssh_keys(self) -> str:
        """Hardcoded Name"""
        pass

    @validator
    def subnet(self, cs_subnet: str) -> str:
        """quali-CS_Subnet"""
        return f"{GCP_NAME_PREFIX}-{re.sub('[ _.]', '-', cs_subnet.lower().replace('-', '--'))}"

    @validator
    def network(self, reservation_id: str) -> str:
        """quali-reservationID"""
        return f"{GCP_NAME_PREFIX}-{reservation_id}"

    @validator
    def instance(self, app_name: str, generate: bool = True) -> str:
        """1. verify app_name and set or raise 2. generate vm name based on app_name"""
        if generate:
            postfix = generate_short_unique_string()
            instance_name = re.sub(f"[{re.escape(CS_ALLOWED_SYMBOLS)}]+", '-', f"{app_name.lower()[:self.max_length-len(postfix)-1]}-{postfix}")
        else:
            instance_name = app_name

        return instance_name

    @validator
    def instance_disk(self, instance_name: str, disk_num: int) -> str:
        """instance_name-disk-1"""
        return f"{instance_name}-disk-{disk_num}"

    @validator
    def iface(self, instance_name: str, iface_num: int) -> str:
        """instance_name-disk-1"""
        return f"{instance_name}-iface-{iface_num}"

    @validator
    def firewall_rule(
        self,
        instance_name: str,
        src_cidr: str,
        dst_port: int,
        protocol: str
    ) -> str:
        """quali-instance_name-dst-dst_port-protocol"""
        return f"{GCP_NAME_PREFIX}-{instance_name}-{src_cidr.replace('/', '--').replace('.', '-')}-{dst_port}-{protocol.lower()}"

    @validator
    def firewall_policy(self, instance_name: str) -> str:
        """quali-instance_name"""
        return f"{GCP_NAME_PREFIX}-{instance_name}"

    @validator
    def public_ip(self, instance_name: str) -> str:
        """quali-instance_name-public-ip"""
        return f"{GCP_NAME_PREFIX}-{instance_name}-public-ip"

    @validator
    def route(self, reservation_id: str, dst: str) -> str:
        """quali-reservationID-dst"""
        return f"{GCP_NAME_PREFIX}-{reservation_id}-{dst}"
