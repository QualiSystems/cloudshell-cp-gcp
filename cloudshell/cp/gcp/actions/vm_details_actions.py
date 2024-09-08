from __future__ import annotations

import re
import typing
from logging import Logger

from attr import define
from cloudshell.cp.core.request_actions.models import (
    VmDetailsData,
    VmDetailsNetworkInterface,
    VmDetailsProperty,
)
from cloudshell.cp.gcp.helpers.interface_helper import InterfaceHelper

if typing.TYPE_CHECKING:
    from cloudshell.cp.gcp.resource_conf import GCPResourceConfig


@define
class VMDetailsActions:
    config: GCPResourceConfig
    logger: Logger

    @staticmethod
    def _parse_image_name(resource_id):
        """Get image name from the Azure image reference ID.

        :param str resource_id: Azure image reference ID
        :return: Azure image name
        :rtype: str
        """
        match_images = re.match(
            r".*images/(?P<image_name>[^/]*).*", resource_id, flags=re.IGNORECASE
        )
        return match_images.group("image_name") if match_images else ""

    @staticmethod
    def _parse_resource_group_name(resource_id):
        """Get resource group name from the Azure resource ID.

        :param str resource_id: Azure resource ID
        :return: Azure resource group name
        :rtype: str
        """
        match_groups = re.match(
            r".*resourcegroups/(?P<group_name>[^/]*)/.*",
            resource_id,
            flags=re.IGNORECASE,
        )
        return match_groups.group("group_name") if match_groups else ""

    @staticmethod
    def _prepare_common_vm_instance_data(instance, resource_group_name: str):
        """Prepare common VM instance data."""
        os_disk = instance.storage_profile.os_disk
        # os_disk_type = convert_azure_to_cs_disk_type(
        #     azure_disk_type=os_disk.managed_disk.storage_account_type
        # )
        if isinstance(instance.storage_profile.os_disk.os_type, str):
            os_name = instance.storage_profile.os_disk.os_type
        else:
            os_name = instance.storage_profile.os_disk.os_type.name

        vm_properties = [
            VmDetailsProperty(
                key="VM Size", value=instance.hardware_profile.vm_size
            ),
            VmDetailsProperty(
                key="Operating System",
                value=os_name,
            ),
            VmDetailsProperty(
                key="OS Disk Size",
                value=f"{instance.storage_profile.os_disk.disk_size_gb}GB "
                f"({os_disk_type})",
            ),
            VmDetailsProperty(
                key="Resource Group",
                value=resource_group_name,
            ),
        ]

        for disk_number, data_disk in enumerate(
            instance.storage_profile.data_disks, start=1
        ):
            disk_type = convert_azure_to_cs_disk_type(
                azure_disk_type=data_disk.managed_disk.storage_account_type
            )
            disk_name_prop = VmDetailsProperty(
                key=f"Data Disk {disk_number} Name",
                value=get_display_data_disk_name(
                    vm_name=instance.name, full_disk_name=data_disk.name
                ),
            )
            disk_size_prop = VmDetailsProperty(
                key=f"Data Disk {disk_number} Size",
                value=f"{data_disk.disk_size_gb}GB ({disk_type})",
            )
            vm_properties.append(disk_name_prop)
            vm_properties.append(disk_size_prop)

        return vm_properties

    def _prepare_vm_network_data(self, instance):
        """Prepare VM Network data.

        :param instance:
        :param str resource_group_name:
        :return:
        """
        vm_network_interfaces = []
        public_ip = InterfaceHelper(instance).get_public_ip()

        for network_interface in instance.network_interfaces:
            interface_name = get_name_from_resource_id(network_interface.id)
            interface = self.get_vm_network(
                interface_name=interface_name, resource_group_name=resource_group_name
            )

            ip_configuration = interface.ip_configurations[0]
            private_ip_addr = ip_configuration.private_ip_address

            network_data = [
                VmDetailsProperty(key="IP", value=ip_configuration.private_ip_address),
                VmDetailsProperty(key="MAC Address", value=interface.mac_address),
            ]

            subnet_name = ip_configuration.subnet.id.split("/")[-1]

            if ip_configuration.public_ip_address:
                public_ip = self.get_vm_network_public_ip(
                    interface_name=interface_name,
                    resource_group_name=resource_group_name,
                )
                network_data.extend(
                    [
                        VmDetailsProperty(key="Public IP", value=public_ip.ip_address),
                        VmDetailsProperty(
                            key="Public IP Type",
                            value=public_ip.public_ip_allocation_method,
                        ),
                    ]
                )

                public_ip_addr = public_ip.ip_address
            else:
                public_ip_addr = ""

            vm_network_interface = VmDetailsNetworkInterface(
                interfaceId=interface.resource_guid,
                networkId=subnet_name,
                isPrimary=interface.primary,
                networkData=network_data,
                privateIpAddress=private_ip_addr,
                publicIpAddress=public_ip_addr,
            )

            vm_network_interfaces.append(vm_network_interface)

        return vm_network_interfaces

    def _prepare_vm_details(
        self,
        instance,
        prepare_vm_instance_data_function: typing.Callable,
    ):
        """Prepare VM details."""
        try:
            return VmDetailsData(
                appName=instance.name,
                vmInstanceData=prepare_vm_instance_data_function(
                    instance=instance,
                ),
                vmNetworkData=self._prepare_vm_network_data(
                    instance=instance,
                ),
            )
        except Exception as e:
            self._logger.exception(
                f"Error getting VM details for {instance.name}"
            )
            return VmDetailsData(appName=instance.name, errorMessage=str(e))

    def _prepare_vm_instance_data(
        self, instance, resource_group_name: str
    ):
        """Prepare custom VM instance data."""
        image_resource_id = instance.storage_profile.image_reference.id
        image_name = self._parse_image_name(resource_id=image_resource_id)
        image_resource_group = self._parse_resource_group_name(
            resource_id=image_resource_id
        )

        return [
            VmDetailsProperty(key="Image", value=image_name),
            VmDetailsProperty(key="Image Resource Group", value=image_resource_group),
        ] + self._prepare_common_vm_instance_data(
            instance=instance,
            resource_group_name=resource_group_name,
        )

    def prepare_custom_vm_details(self, instance):
        """Prepare custom VM details."""
        return self._prepare_vm_details(
            instance=instance,
            prepare_vm_instance_data_function=self._prepare_vm_instance_data,
        )