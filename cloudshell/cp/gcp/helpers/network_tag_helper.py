import re

from attr import define

from cloudshell.cp.gcp.helpers.name_generator import GCPNameGenerator
from cloudshell.cp.gcp.models.deploy_app import BaseGCPDeployApp

DEFAULT_DESTINATION = "0.0.0.0/0"
DEFAULT_PROTOCOL = "tcp"


@define
class InboundPort:
    port_range: str
    src_address: str = DEFAULT_DESTINATION
    protocol: str = DEFAULT_PROTOCOL



PORT_DATA_MATCH = re.compile(
    r"^(?P<from_port>\d+)"
    r"(-(?P<to_port>\d+))?"
    r"(:(?P<protocol>(all|udp|tcp|icmp)))?"
    r"(:(?P<destination>\S+))?$",
    re.IGNORECASE,
)
ICMP_PORT_DATA_MATCH = re.compile(
    r"^(?P<protocol>icmp)" r"(:(?P<destination>\S+))?$",
    re.IGNORECASE,
)


def get_network_tags(
        app_name: str,
        tags: list[InboundPort]
) -> dict[str, InboundPort]:
    """Get network tags for VM.

    """
    network_tags = {}
    for network_tag in tags:
        name = GCPNameGenerator().firewall_rule(
            instance_name=app_name,
            src_cidr=network_tag.src_address,
            dst_port_range=network_tag.port_range,
            protocol=network_tag.protocol,
        )
        network_tags[name] = tag

    return network_tags


def parse_port_range(port_data):
    """Parse port range.

    """
    match = PORT_DATA_MATCH.search(port_data)
    if match:
        from_port = match.group("from_port")
        to_port = match.group("to_port")
    else:
        # match = self.ICMP_PORT_DATA_MATCH.search(port_data)
        # if match:
        #     from_port = to_port = "-1"
        # else:
        msg = f"The value '{port_data}' is not a valid ports rule"
        raise ValueError(msg)

    destination = match.group("destination") or DEFAULT_DESTINATION
    protocol = match.group("protocol") or DEFAULT_PROTOCOL
    port = f"{from_port}"
    if to_port:
        port = f"{from_port}-{to_port}"
    return InboundPort(port, protocol, destination)