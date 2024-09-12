import re

from attr import define

from cloudshell.cp.gcp.models.deploy_app import BaseGCPDeployApp

DEFAULT_DESTINATION = "0.0.0.0/0"
DEFAULT_PROTOCOL = "tcp"


@define
class InboundPort:
    port_range: str
    src_address: str = DEFAULT_DESTINATION
    protocol: str = DEFAULT_PROTOCOL


@define
class NetworkTagHelper:
    PORT_DATA_MATCH = re.compile(
        r"^(?P<from_port>\d+)"
        r"(-(?P<to_port>\d+))?"
        r"(:(?P<protocol>(udp|tcp|icmp)))?"
        r"(:(?P<destination>\S+))?$",
        re.IGNORECASE,
    )
    ICMP_PORT_DATA_MATCH = re.compile(
        r"^(?P<protocol>icmp)" r"(:(?P<destination>\S+))?$",
        re.IGNORECASE,
    )


    CUSTOM_NSG_RULE_NAME_TPL = (
        "rule-{vm_name}-{dst_address}-"
        "{dst_port_range}-{protocol}"
    )
    deploy_app: BaseGCPDeployApp

    def get_network_tags(self, app_name) -> dict[str,InboundPort]:
        """Get network tags for VM.

        :param app_name: VM name
        :return: Network tags
        """
        # ToDo adjust this one for work in deploy app parser.
        network_tags = {}
        for network_tag in self.deploy_app.inbound_ports:
            rule = self._parse_port_range(network_tag)
            name = self.CUSTOM_NSG_RULE_NAME_TPL.format(
                vm_name=app_name,
                dst_address=rule.dst_address,
                dst_port_range=rule.dst_port_range,
                protocol=rule.protocol,
            )
            network_tags[name] = self._parse_port_range(network_tag)

        return network_tags

    def _parse_port_range(self, port_data):
        match = self.PORT_DATA_MATCH.search(port_data)
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

        destination = match.group("destination") or self.DEFAULT_DESTINATION
        protocol = match.group("protocol") or self.DEFAULT_PROTOCOL
        port = f"{from_port}"
        if to_port:
            port = f"{from_port}-{to_port}"
        return InboundPort(port, protocol, destination)