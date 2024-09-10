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
    from cloudshell.cp.gcp.handlers.instance import Instance


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
    def _prepare_common_vm_instance_data(instance, resource_group_name: str):
        """Prepare common VM instance data."""
        disks = instance.disks
        os_disk = instance.disks[0]
        # os_disk_type = convert_azure_to_cs_disk_type(
        #     azure_disk_type=os_disk.managed_disk.storage_account_type
        # )
        if isinstance(instance.storage_profile.os_disk.os_type, str):
            os_name = instance.storage_profile.os_disk.os_type
        else:
            os_name = instance.storage_profile.os_disk.os_type.name

        vm_properties = [
            VmDetailsProperty(
                key="VM Size", value=instance.machine_type
            ),
            VmDetailsProperty(
                key="Operating System",
                value=os_name,
            ),
            # VmDetailsProperty(
            #     key="OS Disk Size",
            #     value=f"{instance.storage_profile.os_disk.disk_size_gb}GB "
            #     f"({os_disk_type})",
            # ),
            VmDetailsProperty(
                key="Resource Group",
                value=resource_group_name,
            ),
        ]

        for disk_number, data_disk in enumerate(
            instance.disks, start=1
        ):
            if data_disk.boot:
                vm_properties.append(VmDetailsProperty(
                key="OS Disk Size",
                value=f"{instance.storage_profile.os_disk.disk_size_gb}GB "
                f"({instance.storage_profile.os_disk.disk_type})",))

            # else:
                # disk_type = convert_azure_to_cs_disk_type(
                #     azure_disk_type=data_disk.managed_disk.storage_account_type
                # )
                # disk_name_prop = VmDetailsProperty(
                #     key=f"Data Disk {disk_number} Name",
                #     value=get_display_data_disk_name(
                #         vm_name=instance.name, full_disk_name=data_disk.name
                #     ),
                # )
                # disk_size_prop = VmDetailsProperty(
                #     key=f"Data Disk {disk_number} Size",
                #     value=f"{data_disk.disk_size_gb}GB ({disk_type})",
                # )
                # vm_properties.append(disk_name_prop)
                # vm_properties.append(disk_size_prop)

        return vm_properties

    def _prepare_vm_network_data(self, instance: Instance):
        """Prepare VM Network data.

        :param instance:
        :param str resource_group_name:
        :return:
        """
        vm_network_interfaces = []


        for network_interface in instance.network_interfaces:
            is_primary = False
            index = instance.network_interfaces.index(network_interface)
            if index == 0:
                is_primary = True
            interface_name = network_interface.name

            private_ip = network_interface.network_i_p
            # nic_type
            public_ip = InterfaceHelper(instance).get_public_ip(index)
            network_data = [
                # VmDetailsProperty(key="IP", value=private_ip),
            ]

            subnet_name = network_interface.subnetwork

            if public_ip:
                network_data.extend(
                    [
                        VmDetailsProperty(
                            key="Public IP Kind",
                            value=network_interface.access_configs[0].kind,
                        ),
                        VmDetailsProperty(key='Name', value=interface_name)
                    ]
                )

            vm_network_interface = VmDetailsNetworkInterface(
                interfaceId=index,
                networkId=subnet_name.split('/')[-1],
                isPrimary=is_primary,
                networkData=network_data,
                privateIpAddress=private_ip,
                publicIpAddress=public_ip,
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
            VmDetailsProperty(key="Image Project", value=image_resource_group),
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