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

from cloudshell.cp.gcp.handlers.disk import DiskHandler
from cloudshell.cp.gcp.handlers.image import ImageHandler
from cloudshell.cp.gcp.helpers.constants import PUBLIC_IMAGE_PROJECTS
from cloudshell.cp.gcp.helpers.interface_helper import InterfaceHelper

if typing.TYPE_CHECKING:
    from cloudshell.cp.gcp.resource_conf import GCPResourceConfig
    from cloudshell.cp.gcp.handlers.instance import InstanceHandler


@define
class VMDetailsActions:
    config: GCPResourceConfig
    logger: Logger

    @staticmethod
    def _prepare_common_vm_instance_data(instance_handler: InstanceHandler):
        """Prepare common VM instance data."""
        instance = instance_handler.instance
        vm_properties = [
            VmDetailsProperty(
                key="Machine Type", value=instance.machine_type.rsplit('/', 1)[-1],
            ),
        ]

        disks = list(instance.disks)
        os_disk = next((disk for disk in disks if disk.boot), None)
        disks.remove(os_disk)
        if os_disk:
            os_disk_data = DiskHandler.get(
                disk_name=os_disk.source.rsplit('/', 1)[-1],
                zone=instance.zone.rsplit('/', 1)[-1],
                credentials=instance_handler.credentials,
            )
            image_data = ImageHandler.parse_image_name(
                image_url=os_disk_data.source_image,
            )

            image_name = image_data.get("image_name", "N/A")
            image_project = image_data.get("image_project", "N/A")
            image_project = next(
                    (k for k, v in PUBLIC_IMAGE_PROJECTS.items() if v == image_project),
                    image_project)
            disk_type = os_disk_data.disk_type
            disk_size = os_disk_data.disk_size
            vm_properties.extend(
                [
                    VmDetailsProperty(key="Instance Arch",
                                      value=f"{os_disk_data.architecture.lower()}", ),
                    VmDetailsProperty(key="OS Disk Size",
                                      value=f"{disk_size}GB ({disk_type})", ),
                    VmDetailsProperty(key="Image Name", value=image_name),
                    VmDetailsProperty(key="Image Project", value=image_project),
                ]
            )

        for disk_number, data_disk in enumerate(
            disks, start=1
        ):
            disk_data = DiskHandler.get(
                disk_name=data_disk.name,
                zone=instance.zone.rsplit('/', 1)[-1],
                credentials=instance_handler.credentials,
            )
            disk_name_prop = VmDetailsProperty(
                key=f"Data Disk {disk_number} Name",
                value=disk_data.disk.name,
            )
            disk_size_prop = VmDetailsProperty(
                key=f"Data Disk {disk_number} Size",
                value=f"{data_disk.disk_size}GB ({disk_data.disk_type})",
            )
            vm_properties.append(disk_name_prop)
            vm_properties.append(disk_size_prop)

        return vm_properties

    def _prepare_vm_network_data(self, instance_handler: InstanceHandler):
        """Prepare VM Network data.

        :param instance:
        :param str resource_group_name:
        :return:
        """
        vm_network_interfaces = []


        for network_interface in instance_handler.instance.network_interfaces:
            is_primary = False
            index = instance_handler.instance.network_interfaces.index(
                network_interface)
            if index == 0:
                is_primary = True
            interface_name = network_interface.name

            private_ip = network_interface.network_i_p
            public_ip = InterfaceHelper(instance_handler.instance).get_public_ip(index)
            network_data = []

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
                networkId=subnet_name[subnet_name.find("/project"):],
                isPrimary=is_primary,
                networkData=network_data,
                privateIpAddress=private_ip,
                publicIpAddress=public_ip,
            )

            vm_network_interfaces.append(vm_network_interface)

        return vm_network_interfaces

    def _prepare_vm_details(
        self,
        instance_handler: InstanceHandler,
        prepare_vm_instance_data_function: typing.Callable,
    ):
        """Prepare VM details."""
        try:
            return VmDetailsData(
                appName=instance_handler.instance.name,
                vmInstanceData=prepare_vm_instance_data_function(
                    instance_handler=instance_handler,
                ),
                vmNetworkData=self._prepare_vm_network_data(
                    instance_handler=instance_handler,
                ),
            )
        except Exception as e:
            self.logger.exception(
                f"Error getting VM details for {instance_handler.instance.name}"
            )
            return VmDetailsData(appName=instance_handler.instance.name,
                                 errorMessage=str(e))

    def prepare_vm_details(self, instance_handler: InstanceHandler):
        """Prepare custom VM details."""
        return self._prepare_vm_details(
            instance_handler=instance_handler,
            prepare_vm_instance_data_function=self._prepare_common_vm_instance_data,
        )