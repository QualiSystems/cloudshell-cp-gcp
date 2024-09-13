from __future__ import annotations

import logging
from functools import cached_property
from typing import TYPE_CHECKING

from attrs import define
from google.cloud import compute_v1
from google.cloud.compute_v1.types import compute

from cloudshell.cp.gcp.handlers.base import BaseGCPHandler
from cloudshell.cp.gcp.helpers.name_generator import GCPNameGenerator
from cloudshell.cp.gcp.helpers.errors import AttributeGCPError
from cloudshell.cp.gcp.models.deploy_app import (
    InstanceFromScratchDeployApp,
    InstanceFromTemplateDeployApp,
    InstanceFromMachineImageDeployApp,
)

if TYPE_CHECKING:
    from google.auth.credentials import Credentials
    from typing_extensions import Self, Union, Iterable
    from cloudshell.cp.gcp.resource_conf import GCPResourceConfig

logger = logging.getLogger(__name__)


@define
class Instance:
    deploy_app: Union[InstanceFromScratchDeployApp, InstanceFromTemplateDeployApp,
                 InstanceFromMachineImageDeployApp]
    resource_config: GCPResourceConfig
    subnet_list: list[str]

    def from_scratch(self):
        """Build GCP Instance from scratch."""
        # Define the VM settings
        instance = compute_v1.Instance()
        instance.name = GCPNameGenerator().instance(
            app_name=self.deploy_app.app_name,
            generate=self.deploy_app.autogenerated_name
        )
        instance.can_ip_forward = self.deploy_app.ip_forwarding
        instance.machine_type = f"zones/{self.deploy_app.zone}/machineTypes/{self.deploy_app.machine_type}"

        # instance.tags = ["str", "str"]

        scheduling = compute_v1.Scheduling()
        scheduling.automatic_restart = self.deploy_app.auto_restart
        scheduling.on_host_maintenance = self.deploy_app.maintenance.upper()
        instance.scheduling = scheduling

        # Create boot disk
        boot_disk = compute_v1.AttachedDisk()
        boot_disk.boot = True
        boot_disk.device_name = GCPNameGenerator().instance_disk(
            instance_name=instance.name,
            disk_num=0
        )
        # boot_disk.auto_delete = self.deploy_app.disk_rule
        disk_initialize_params = compute_v1.AttachedDiskInitializeParams()
        disk_initialize_params.disk_size_gb = self.deploy_app.disk_size
        disk_initialize_params.disk_type = f"zones/{self.deploy_app.zone}/diskTypes/{self.deploy_app.disk_type}"
        #                                       projects/debian-cloud/global/images/debian-12-bookworm-v20240910
        disk_initialize_params.source_image = f"projects/{self.deploy_app.project_cloud}/global/images/{self.deploy_app.disk_image}"
        boot_disk.initialize_params = disk_initialize_params
        instance.disks = [boot_disk]

        # Create Network Interfaces
        self._add_interfaces(instance)

        # Create Metadata (CS Tags)
        custom_tags = compute_v1.Metadata()
        items = []
        for tag in self.deploy_app.custom_tags.items():
            item = compute_v1.Items()
            item.key, item.value = tag
            items.append(item)
        custom_tags.items = items
        instance.metadata = custom_tags

        return instance

    def from_template(self):
        """"""

        template_client = compute_v1.InstanceTemplatesClient(
            credentials=self.resource_config.credentials
        )

        # Get the instance template
        instance_template = template_client.get(
            project=self.resource_config.project_id,
            instance_template=self.deploy_app.template_name
        )

        # Prepare instance configuration based on the template
        instance = compute_v1.Instance()
        instance.name = GCPNameGenerator().instance(
            app_name=self.deploy_app.app_name,
            generate=self.deploy_app.autogenerated_name
        )

        instance.can_ip_forward = self.deploy_app.ip_forwarding or instance_template.properties.can_ip_forward
        instance.machine_type = f"zones/{self.deploy_app.zone}/machineTypes/{self.deploy_app.machine_type}" or instance_template.properties.machine_type

        # instance.tags = ["str", "str"]

        scheduling = compute_v1.Scheduling()
        scheduling.automatic_restart = self.deploy_app.auto_restart or instance_template.properties.scheduling.automatic_restart
        scheduling.on_host_maintenance = self.deploy_app.maintenance or instance_template.properties.scheduling.on_host_maintenance
        instance.scheduling = scheduling

        # Create disks
        for disk in instance_template.properties.disks:
            attached_disk = compute_v1.AttachedDisk()
            if disk.boot:
                attached_disk.auto_delete = disk.auto_delete
                attached_disk.boot = disk.boot

                disk_initialize_params = compute_v1.AttachedDiskInitializeParams()
                disk_initialize_params.disk_size_gb = self.deploy_app.disk_size or disk.initialize_params.disk_size_gb
                if self.deploy_app.disk_type:
                    disk_initialize_params.disk_type = f"zones/{self.deploy_app.zone}/diskTypes/{self.deploy_app.disk_type}"
                else:
                    disk_initialize_params.disk_type = disk.initialize_params.disk_type

                if self.deploy_app.disk_image:
                    disk_initialize_params.source_image = f"projects/{self.deploy_app.project_cloud}/global/images/{self.deploy_app.disk_image}"
                else:
                    disk_initialize_params.source_image = disk.initialize_params.source_image

                attached_disk.initialize_params = disk_initialize_params
            else:
                attached_disk.auto_delete = disk.auto_delete
                attached_disk.boot = disk.boot
                attached_disk.type_ = disk.type_
                attached_disk.initialize_params = disk.initialize_params

            instance.disks.append(attached_disk)

        # Create Network Interfaces
        # instance.network_interfaces = instance_template.properties.network_interfaces
        self._add_interfaces(instance)

        # Create Metadata (CS Tags)
        custom_tags = compute_v1.Metadata()
        items = []
        for tag in self.deploy_app.custom_tags.items():
            item = compute_v1.Items()
            item.key, item.value = tag
            items.append(item)
        custom_tags.items = items
        instance.metadata = custom_tags

        return instance

    def from_machine_image(self): # machine_image.source_instance_properties
        """"""
        machine_image_client = compute_v1.MachineImagesClient(
            credentials=self.resource_config.credentials
        )

        # Get the machine image
        machine_image = machine_image_client.get(
            project=self.resource_config.project_id,
            machine_image=self.deploy_app.machine_image_name
        )

        # Prepare the instance configuration
        # Prepare instance configuration based on the template
        instance = compute_v1.Instance()
        instance.name = GCPNameGenerator().instance(
            app_name=self.deploy_app.app_name,
            generate=self.deploy_app.autogenerated_name
        )

        instance.can_ip_forward = self.deploy_app.ip_forwarding or machine_image.source_instance_properties.can_ip_forward
        instance.machine_type = f"zones/{self.deploy_app.zone}/machineTypes/{self.deploy_app.machine_type}" or machine_image.source_instance_properties.properties.machine_type

        # instance.tags = ["str", "str"]

        scheduling = compute_v1.Scheduling()
        scheduling.automatic_restart = self.deploy_app.auto_restart or machine_image.source_instance_properties.scheduling.automatic_restart
        scheduling.on_host_maintenance = (self.deploy_app.maintenance or
                                          machine_image.source_instance_properties.scheduling.on_host_maintenance).upper()
        instance.scheduling = scheduling

        # Create disks
        for disk in machine_image.source_instance_properties.disks:
            attached_disk = compute_v1.AttachedDisk()
            attached_disk.auto_delete = disk.auto_delete
            attached_disk.boot = disk.boot
            attached_disk.type_ = disk.type_
            attached_disk.initialize_params = disk.initialize_params
            instance.disks.append(attached_disk)

        # Create Network Interfaces
        # instance.network_interfaces = machine_image.source_instance_properties.network_interfaces
        self._add_interfaces(instance)

        # Create Metadata (CS Tags)
        custom_tags = compute_v1.Metadata()
        items = []
        for tag in self.deploy_app.custom_tags.items():
            item = compute_v1.Items()
            item.key, item.value = tag
            items.append(item)
        custom_tags.items = items
        instance.metadata = custom_tags

        return instance

    def _add_interfaces(self, instance):
        for subnet_num, subnet in enumerate(self.subnet_list):
            network_interface = compute_v1.NetworkInterface()
            network_interface.name = GCPNameGenerator().iface(
                instance_name=instance.name,
                iface_num=subnet_num
            )
            network_interface.subnetwork = subnet

            access_config = compute_v1.AccessConfig()
            access_config.name = network_interface.name
            access_config.type_ = "ONE_TO_ONE_NAT"
            network_interface.access_configs = [access_config]

            instance.network_interfaces.append(network_interface)


@define
class InstanceHandler(BaseGCPHandler):
    instance: compute.Instance

    @cached_property
    def instance_client(self):
        return compute_v1.InstancesClient(credentials=self.credentials)

    @classmethod
    def deploy(
            cls,
            instance: compute.Instance,
            credentials: Credentials,
            zone: str
    ) -> Self:
        """Get instance object from GCP and create InstanceHandler object."""
        logger.info("Start deploying Instance.")
        client = compute_v1.InstancesClient(credentials=credentials)

        operation = client.insert(
            project=credentials.project_id,
            zone=zone,
            instance_resource=instance
        )

        # Wait for the operation to complete
        operation_client = compute_v1.ZoneOperationsClient(
            credentials=credentials
        )
        operation_client.wait(
            project=credentials.project_id,
            zone=zone,
            operation=operation.name
        )
        logger.info(f"Instance '{instance.name}' created successfully.")
        if operation.done and operation.error:
            raise Exception(f"Instance {instance.name} deployment failed: "
                            f"{operation.error_code} - {operation.error_message}")
        return cls.get(
            credentials=credentials,
            zone=zone,
            instance_name=instance.name
        )

    @classmethod
    def get(cls, instance_name: str, zone: str, credentials: Credentials) -> Self:
        """Get instance object from GCP and create InstanceHandler object."""
        logger.info("Getting Instance.")
        client = compute_v1.InstancesClient(credentials=credentials)
        instance = client.get(
            project=credentials.project_id,
            zone=zone,
            instance=instance_name
        )
        return cls(instance=instance, credentials=credentials)

    @property
    def _zone(self):
        return self.instance.zone.rsplit('/', 1)[-1]

    # def zone_checker(self):
    #     def decorator(func):
    #         def wrapper(*args, **kwargs):
    #             if not kwargs.get("zone"):
    #                 if self.zone:
    #                     kwargs.update({"zone": self.zone})
    #                 else:
    #                     if self.region:
    #                         zones = self.get_zones(region=self.region)
    #                         zone = random.choice(zones)
    #                         kwargs.update({"zone": zone.name})
    #                     else:
    #                         raise AttributeGCPError("Region cannot be empty.")  # TODO error message
    #             operation = func(*args, **kwargs)
    #             return operation
    #         return wrapper
    #     return decorator

    def delete(self) -> None:
        """Delete Virtual Machine instance."""
        operation = self.instance_client.delete(
            project=self.credentials.project_id,
            zone=self._zone,
            instance=self.instance.name
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=self._zone)

        logger.info(f"Instance '{self.instance.name}' deleted successfully.")

    def start(self) -> None:
        """Power On Virtual Machine."""
        operation = self.instance_client.start(
            project=self.credentials.project_id, zone=self._zone, instance=self.instance.name
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=self._zone)

        logger.info(f"VM '{self.instance.name}' started successfully.")

    def stop(self) -> None:
        """Power Off Virtual Machine."""
        operation = self.instance_client.stop(
            project=self.credentials.project_id, zone=self._zone, instance=self.instance.name
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=self._zone)

        logger.info(f"VM '{self.instance.name}' stopped successfully.")

    def add_metadata(self, vm_name: str, key: str, value: str, *, zone: str) -> None:
        """Add metadata record."""
        # Get the existing VM
        vm = self.get_vm_by_name(vm_name, zone)

        # Add the new metadata
        vm.metadata.items.append({"key": key, "value": value})

        # Update the VM
        operation = self.instance_client.update(
            project=self.credentials.project_id,
            zone=self._zone,
            instance=self.instance.name,
            instance_resource=vm,
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=self._zone)

        logger.info(f"Metadata '{key}={value}' added to VM '{self.instance.name}'.")

    def remove_metadata(self, vm_name: str, key: str, *, zone: str) -> None:
        """Remove metadata record."""
        # Get the existing VM
        vm = self.get_vm_by_name(vm_name, zone)

        # Remove the metadata
        for item in vm.metadata.items:
            if item.key == key:
                vm.metadata.items.remove(item)

        # Update the VM
        operation = self.instance_client.update(
            project=self.credentials.project_id,
            zone=self._zone,
            instance=self.instance.name,
            instance_resource=vm,
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=self._zone)

        logger.info(f"Metadata '{key}' removed from VM '{self.instance.name}'.")

    def add_network_interface(
            self,
            vm_name: str,
            network_name: str,
            subnet_name: str,
            *,
            zone: str
    ) -> None:
        """Add Network interface to existed Virtual Machine instance."""
        # Get the existing VM
        vm = self.get_vm_by_name(vm_name, zone)

        # Add the new network interface
        vm.network_interfaces.append(
            {
                "network": f"projects/{self.credentials.project_id}/global/networks/{network_name}",
                "subnetwork": f"projects/{self.credentials.project_id}/regions/{zone[:-2]}/subnetworks/{subnet_name}",
            }
        )

        # Update the VM
        operation = self.instance_client.update(
            project=self.credentials.project_id,
            zone=self._zone,
            instance=self.instance.name,
            instance_resource=vm,
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=self._zone)

        logger.info(f"Network interface added to VM '{self.instance.name}'.")

    def remove_network_interface(
        self, vm_name: str, network_name: str, subnet_name: str, *, zone: str
    ) -> None:
        """Delete Network Interface from Virtual Machine."""
        # Get the existing VM
        vm = self.get_vm_by_name(vm_name, zone)

        # Remove the network interface
        for interface in vm.network_interfaces:
            if (
                interface.network
                == f"projects/{self.credentials.project_id}/global/networks/{network_name}"
                and interface.subnetwork
                == f"projects/{self.credentials.project_id}/regions/{zone[:-2]}/subnetworks/{subnet_name}"
            ):
                vm.network_interfaces.remove(interface)

        # Update the VM
        operation = self.instance_client.update(
            project=self.credentials.project_id,
            zone=self._zone,
            instance=self.instance.name,
            instance_resource=vm,
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=self._zone)

        logger.info(f"Network interface removed from VM '{self.instance.name}'.")

    def add_disk(
            self,
            vm_name: str,
            disk_name: str,
            disk_type: str,
            disk_size_gb: float,
            source_image: str,
            *,
            zone: str
    ) -> None:
        """Add disk to Virtual Machine."""
        # Get the existing VM
        vm = self.get_vm_by_name(vm_name, zone)

        # Add the new disk
        vm.disks.append(
            {
                "name": disk_name,
                "type": disk_type,
                "size_gb": disk_size_gb,
                "source_image": f"projects/{source_image}/global/images/family/{source_image}",
            }
        )

        # Update the VM
        operation = self.instance_client.update(
            project=self.credentials.project_id,
            zone=self._zone,
            instance=self.instance.name,
            instance_resource=vm,
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=self._zone)

        logger.info(f"Disk '{disk_name}' added to VM '{self.instance.name}'.")

    def remove_disk(self, vm_name: str, disk_name: str, *, zone: str) -> None:
        """Remove disk from Virtual Machine."""
        # Get the existing VM
        vm = self.get_vm_by_name(vm_name, zone)

        # Remove the disk
        for disk in vm.disks:
            if disk.name == disk_name:
                vm.disks.remove(disk)

        # Update the VM
        operation = self.instance_client.update(
            project=self.credentials.project_id,
            zone=self._zone,
            instance=self.instance.name,
            instance_resource=vm,
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=self._zone)

        logger.info(f"Disk '{disk_name}' removed from VM '{self.instance.name}'.")

    def add_access_config(
        self, vm_name: str, network_name: str, external_ip: str, *, zone: str
    ) -> None:
        """Add Access List Configuration."""
        # Get the existing VM
        vm = self.get_vm_by_name(vm_name, zone)

        # Add the new access config
        vm.network_interfaces[0].access_configs.append(
            {
                "name": "External NAT",
                "type": "ONE_TO_ONE_NAT",
                "nat_ip": external_ip,
                "network_tier": "PREMIUM",
            }
        )

        # Update the VM
        operation = self.instance_client.update(
            project=self.credentials.project_id,
            zone=self._zone,
            instance=self.instance.name,
            instance_resource=vm,
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=self._zone)

        logger.info(f"Access config added to VM '{self.instance.name}'.")

    def remove_access_config(self, vm_name: str, external_ip: str, *, zone: str) -> None:
        """Remove Access List Configuration."""
        # Get the existing VM
        vm = self.get_vm_by_name(vm_name, zone)

        # Remove the access config
        for config in vm.network_interfaces[0].access_configs:
            if config.nat_ip == external_ip:
                vm.network_interfaces[0].access_configs.remove(config)

        # Update the VM
        operation = self.instance_client.update(
            project=self.credentials.project_id,
            zone=self._zone,
            instance=self.instance.name,
            instance_resource=vm,
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=self._zone)

        logger.info(f"Access config removed from VM '{self.instance.name}'.")

    def add_firewall_rule(
        self, vm_name: str, security_group_name: str, *, zone: str
    ) -> None:
        """Add Firewall Rule."""
        # Get the existing VM
        vm = self.get_vm_by_name(vm_name, zone)

        # Add the new firewall rule
        vm.firewall_rules.append(security_group_name)

        # Update the VM
        operation = self.instance_client.update(
            project=self.credentials.project_id,
            zone=self._zone,
            instance=self.instance.name,
            instance_resource=vm,
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=self._zone)

        logger.info(f"Firewall rule added to VM '{self.instance.name}'.")

    def remove_firewall_rule(
        self, vm_name: str, security_group_name: str, *, zone: str
    ) -> None:
        """Remove Firewall Rule."""
        # Get the existing VM
        vm = self.get_vm_by_name(vm_name, zone)

        # Remove the firewall rule
        vm.firewall_rules.remove(security_group_name)

        # Update the VM
        operation = self.instance_client.update(
            project=self.credentials.project_id,
            zone=self._zone,
            instance=self.instance.name,
            instance_resource=vm,
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=self._zone)

        logger.info(f"Firewall rule removed from VM '{self.instance.name}'.")

    def add_service_account(
        self, vm_name: str, service_account_email: str, *, zone: str
    ) -> None:
        """Add Service Account configuration."""
        # Get the existing VM
        vm = self.get_vm_by_name(vm_name, zone)

        # Add the new service account
        vm.service_accounts.append(
            {
                "email": service_account_email,
                "scopes": ["https://www.googleapis.com/auth/cloud-platform"],
            }
        )

        # Update the VM
        operation = self.instance_client.update(
            project=self.credentials.project_id,
            zone=self._zone,
            instance=self.instance.name,
            instance_resource=vm,
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=self._zone)

        logger.info(f"Service account added to VM '{self.instance.name}'.")

    def remove_service_account(
        self, vm_name: str, service_account_email: str, *, zone: str
    ) -> None:
        """Remove Service Account configuration."""
        # Get the existing VM
        vm = self.get_vm_by_name(vm_name, zone)

        # Remove the service account
        for account in vm.service_accounts:
            if account.email == service_account_email:
                vm.service_accounts.remove(account)

        # Update the VM
        operation = self.instance_client.update(
            project=self.credentials.project_id,
            zone=self._zone,
            instance=self.instance.name,
            instance_resource=vm,
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=self._zone)

        logger.info(f"Service account removed from VM '{self.instance.name}'.")

    def add_public_key(self, vm_name: str, key: str, *, zone: str) -> None:
        """Add Public Key."""
        # Get the existing VM
        vm = self.get_vm_by_name(vm_name, zone)

        # Add the new public key
        vm.metadata.items.append({"key": "ssh-keys", "value": key})

        # Update the VM
        operation = self.instance_client.update(
            project=self.credentials.project_id,
            zone=self._zone,
            instance=self.instance.name,
            instance_resource=vm,
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=self._zone)

        logger.info(f"Public key added to VM '{self.instance.name}'.")

    def add_public_static_ip(self, vm_name: str, ip: str, *, zone: str) -> None:
        """Add Public Static IP."""
        # Get the existing VM
        vm = self.get_vm_by_name(vm_name, zone)

        # Add the new public static IP
        vm.network_interfaces[0].access_configs.append(
            {
                "name": "External NAT",
                "type": "ONE_TO_ONE_NAT",
                "nat_ip": ip,
                "network_tier": "PREMIUM",
            }
        )

        # Update the VM
        operation = self.instance_client.update(
            project=self.credentials.project_id,
            zone=self._zone,
            instance=self.instance.name,
            instance_resource=vm,
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=self._zone)

        logger.info(f"Public static IP added to VM '{self.instance.name}'.")

    def remove_public_static_ip(self, vm_name: str, ip: str, *, zone: str) -> None:
        """Remove Public Static IP."""
        # Get the existing VM
        vm = self.get_vm_by_name(vm_name, zone)

        # Remove the public static IP
        for config in vm.network_interfaces[0].access_configs:
            if config.nat_ip == ip:
                vm.network_interfaces[0].access_configs.remove(config)

        # Update the VM
        operation = self.instance_client.update(
            project=self.credentials.project_id,
            zone=self._zone,
            instance=self.instance.name,
            instance_resource=vm,
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=self._zone)

        logger.info(f"Public static IP removed from VM '{self.instance.name}'.")

    @staticmethod
    def add_network_tags(tags: Iterable[str]) -> compute.Tags:
        """Add network tags to the instance."""
        gcp_tags = compute_v1.Tags()
        gcp_tags.items = list(tags)
        return gcp_tags

"""
class Instance(compute.Instance):

    def _get_zone(self) -> us-central1-a not long URL
    
    @classmethod
    get_instance(cls, name, res_config.credentials) -> self == compute.Instance
    
    @classmethod
    def deploy(cls, deploy_app, res_config, list[network tags]) -> self == compute.Instance
    def deploy(cls, deploy_app, res_config.region, res_config.credentials, res_config.machine_type) -> self == compute.Instance
        
    
    def delete(self):
        operation = self.instance_client.delete(
            project=self.credentials.project_id, zone=self.zone, instance=self.name
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=self._zone)

        logger.info(f"VM '{vm_name}' deleted successfully.")
    
    def start(self)
    
    def stop(self)



machine type

zone - none
region exist

get_all_zones in region
for zone in zones
    check machine type in zone




Instance ->
get_zone

deploy app
    zone
    machine_type    - zone
resource
    region


    from_scratch 
    from_template -> compute.Instance
    from_machine_image


InstanceHandler(BaseGCPHandler):
instance: compute.Instance


    @classmethod
    deploy()
    

    @classmethod
    def get_instance_from_gcp(name)


    stop()
    if not self.instance.id:
        raise

    start()


instance obj -> push GCP Server -> get instance 









"""