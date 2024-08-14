from __future__ import annotations

import logging

from attrs import define
from functools import cached_property
from google.cloud import compute_v1
from typing_extensions import TYPE_CHECKING

from cloudshell.cp.gcp.handlers.base import BaseGCPHandler

if TYPE_CHECKING:
    from google.cloud.compute_v1.types import compute

logger = logging.getLogger(__name__)


@define
class VMHandler(BaseGCPHandler):
    zone: str

    @cached_property
    def instance_client(self):
        return compute_v1.InstancesClient(credentials=self.credentials)

    def create(
            self,
            vm_name: str,
            machine_type: str,
            image_project: str,
            image_family: str,
            subnets: list[compute.Subnetwork],
            zone: str,
            tags: dict = None) -> str:
        """Create Virtual Machine."""
        if not zone:
            zone = self.zone

        # Define the VM settings
        vm = compute_v1.Instance()
        vm.name = vm_name
        vm.machine_type = f"projects/{self.credentials.project_id}/zones/{zone}/machineTypes/{machine_type}"
        vm.tags = tags or {}
        vm.network_interfaces = self._prepare_subnets_attachments(subnets)
        vm.disks = [
            {
                "boot": True,
                "auto_delete": True,
                "initialize_params": {
                    "source_image": f"projects/{image_project}/global/images/family/{image_family}",
                }
            }
        ]

        # Create the VM
        operation = self.instance_client.insert(
            project=self.credentials.project_id,
            zone=zone,
            instance_resource=vm
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=zone)

        logger.info(f"VM '{vm_name}' created successfully.")
        return self.get_vm_by_name(vm_name=vm_name, zone=zone).id

    def _prepare_subnets_attachments(
            self,
            subnets: list[compute.Subnetwork]
    ) -> list[dict[str:str]]:
        return [
            {
                "network": f"projects/{self.credentials.project_id}/global/networks/{subnet.network_name}",
                "subnetwork": f"projects/{self.credentials.project_id}/regions/{subnet.region}/subnetworks/{subnet.subnet_name}",
            }
            for subnet in subnets
        ]

    def get_vm_by_name(self, vm_name: str, zone: str) -> compute.Instance:
        """Get VM instance by its name."""
        if not zone:
            zone = self.zone
        logger.info("Getting VM")
        return self.instance_client.get(
            project=self.credentials.project_id,
            zone=zone,
            instance=vm_name
        )

    def get_vms_by_tag_value(
            self,
            tag: str,
            tag_value: str,
            zone: str
    ) -> list[compute.Instance]:
        """Get Virtual Machine instances by tag."""
        if not zone:
            zone = self.zone
        logger.info("Getting VMs")
        vms = self.instance_client.list(project=self.credentials.project_id, zone=zone)

        # Filter VMs by tag value
        return [vm for vm in vms if tag_value in vm.tags.get(tag)]

    def get_vm_by_id(self, vm_id: str, zone: str) -> compute.Instance:
        """Get Virtual Machine instance by its ID."""
        if not zone:
            zone = self.zone
        logger.info("Getting VM")
        return self.instance_client.get(
            project=self.credentials.project_id,
            zone=zone,
            instance=vm_id
        )

    def delete(self, vm_name: str, zone: str) -> None:
        """Delete Virtual Machine instance."""
        if not zone:
            zone = self.zone
        operation = self.instance_client.delete(
            project=self.credentials.project_id,
            zone=zone,
            instance=vm_name
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=zone)

        logger.info(f"VM '{vm_name}' deleted successfully.")

    def start(self, vm_name: str, zone: str) -> None:
        """Power On Virtual Machine."""
        if not zone:
            zone = self.zone
        operation = self.instance_client.start(
            project=self.credentials.project_id,
            zone=zone,
            instance=vm_name
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=zone)

        logger.info(f"VM '{vm_name}' started successfully.")

    def stop(self, vm_name: str, zone: str) -> None:
        """Power Off Virtual Machine."""
        if not zone:
            zone = self.zone
        operation = self.instance_client.stop(
            project=self.credentials.project_id,
            zone=zone,
            instance=vm_name
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=zone)

        logger.info(f"VM '{vm_name}' stopped successfully.")

    def add_tag(self, vm_name: str, zone: str, tag: dict[str: str]) -> None:
        """Add tag to existed Virtual Machine."""
        if not zone:
            zone = self.zone
        # Get the existing VM
        vm = self.get_vm_by_name(vm_name, zone)

        # Add the new tag
        vm.tags.append(tag)

        # Update the VM
        operation = self.instance_client.update(
            project=self.credentials.project_id,
            zone=zone,
            instance=vm_name,
            instance_resource=vm
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=zone)

        logger.info(f"Tag '{tag}' added to VM '{vm_name}'.")

    def remove_tag(self, vm_name: str, zone: str, tag) -> None:
        """Remove tag."""
        if not zone:
            zone = self.zone
        # Get the existing VM
        vm = self.get_vm_by_name(vm_name, zone)

        # Remove the tag
        vm.tags.remove(tag)

        # Update the VM
        operation = self.instance_client.update(
            project=self.credentials.project_id,
            zone=zone,
            instance=vm_name,
            instance_resource=vm
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=zone)

        logger.info(f"Tag '{tag}' removed from VM '{vm_name}'.")

    def add_metadata(self, vm_name: str, zone: str, key: str, value: str) -> None:
        """Add metadata record."""
        if not zone:
            zone = self.zone
        # Get the existing VM
        vm = self.get_vm_by_name(vm_name, zone)

        # Add the new metadata
        vm.metadata.items.append({"key": key, "value": value})

        # Update the VM
        operation = self.instance_client.update(
            project=self.credentials.project_id,
            zone=zone,
            instance=vm_name,
            instance_resource=vm
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=zone)

        logger.info(f"Metadata '{key}={value}' added to VM '{vm_name}'.")

    def remove_metadata(self, vm_name: str, zone: str, key: str) -> None:
        """Remove metadata record."""
        if not zone:
            zone = self.zone
        # Get the existing VM
        vm = self.get_vm_by_name(vm_name, zone)

        # Remove the metadata
        for item in vm.metadata.items:
            if item.key == key:
                vm.metadata.items.remove(item)

        # Update the VM
        operation = self.instance_client.update(
            project=self.credentials.project_id,
            zone=zone,
            instance=vm_name,
            instance_resource=vm
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=zone)

        logger.info(f"Metadata '{key}' removed from VM '{vm_name}'.")

    def add_network_interface(
            self,
            vm_name: str,
            zone: str,
            network_name: str,
            subnet_name: str
    ) -> None:
        """Add Network interface to existed Virtual Machine instance."""
        if not zone:
            zone = self.zone
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
            zone=zone,
            instance=vm_name,
            instance_resource=vm
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=zone)

        logger.info(f"Network interface added to VM '{vm_name}'.")

    def remove_network_interface(
            self,
            vm_name: str,
            zone: str,
            network_name: str,
            subnet_name: str
    ) -> None:
        """Delete Network Interface from Virtual Machine."""
        if not zone:
            zone = self.zone
        # Get the existing VM
        vm = self.get_vm_by_name(vm_name, zone)

        # Remove the network interface
        for interface in vm.network_interfaces:
            if interface.network == f"projects/{self.credentials.project_id}/global/networks/{network_name}" and \
                    interface.subnetwork == f"projects/{self.credentials.project_id}/regions/{zone[:-2]}/subnetworks/{subnet_name}":
                vm.network_interfaces.remove(interface)

        # Update the VM
        operation = self.instance_client.update(
            project=self.credentials.project_id,
            zone=zone,
            instance=vm_name,
            instance_resource=vm
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=zone)

        logger.info(f"Network interface removed from VM '{vm_name}'.")

    def add_disk(
            self,
            vm_name: str,
            zone: str,
            disk_name: str,
            disk_type: str,
            disk_size_gb: float,
            source_image: str
    ) -> None:
        """Add disk to Virtual Machine."""
        if not zone:
            zone = self.zone
        # Get the existing VM
        vm = self.get_vm_by_name(vm_name, zone)

        # Add the new disk
        vm.disks.append({
            "name": disk_name,
            "type": disk_type,
            "size_gb": disk_size_gb,
            "source_image": f"projects/{source_image}/global/images/family/{source_image}",
        })

        # Update the VM
        operation = self.instance_client.update(
            project=self.credentials.project_id,
            zone=zone,
            instance=vm_name,
            instance_resource=vm
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=zone)

        logger.info(f"Disk '{disk_name}' added to VM '{vm_name}'.")

    def remove_disk(
            self,
            vm_name: str,
            zone: str,
            disk_name: str
    ) -> None:
        """Remove disk from Virtual Machine."""
        if not zone:
            zone = self.zone
        # Get the existing VM
        vm = self.get_vm_by_name(vm_name, zone)

        # Remove the disk
        for disk in vm.disks:
            if disk.name == disk_name:
                vm.disks.remove(disk)

        # Update the VM
        operation = self.instance_client.update(
            project=self.credentials.project_id,
            zone=zone,
            instance=vm_name,
            instance_resource=vm
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=zone)

        logger.info(f"Disk '{disk_name}' removed from VM '{vm_name}'.")

    def add_access_config(
            self,
            vm_name: str,
            zone: str,
            network_name: str,
            external_ip: str
    ) -> None:
        """Add Access List Configuration."""
        if not zone:
            zone = self.zone
        # Get the existing VM
        vm = self.get_vm_by_name(vm_name, zone)

        # Add the new access config
        vm.network_interfaces[0].access_configs.append({
            "name": "External NAT",
            "type": "ONE_TO_ONE_NAT",
            "nat_ip": external_ip,
            "network_tier": "PREMIUM",
        })

        # Update the VM
        operation = self.instance_client.update(
            project=self.credentials.project_id,
            zone=zone,
            instance=vm_name,
            instance_resource=vm
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=zone)

        logger.info(f"Access config added to VM '{vm_name}'.")

    def remove_access_config(self, vm_name: str, zone: str, external_ip: str) -> None:
        """Remove Access List Configuration."""
        if not zone:
            zone = self.zone
        # Get the existing VM
        vm = self.get_vm_by_name(vm_name, zone)

        # Remove the access config
        for config in vm.network_interfaces[0].access_configs:
            if config.nat_ip == external_ip:
                vm.network_interfaces[0].access_configs.remove(config)

        # Update the VM
        operation = self.instance_client.update(
            project=self.credentials.project_id,
            zone=zone,
            instance=vm_name,
            instance_resource=vm
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=zone)

        logger.info(f"Access config removed from VM '{vm_name}'.")

    def add_firewall_rule(
            self,
            vm_name: str,
            zone: str,
            security_group_name: str
    ) -> None:
        """Add Firewall Rule."""
        if not zone:
            zone = self.zone
        # Get the existing VM
        vm = self.get_vm_by_name(vm_name, zone)

        # Add the new firewall rule
        vm.firewall_rules.append(security_group_name)

        # Update the VM
        operation = self.instance_client.update(
            project=self.credentials.project_id,
            zone=zone,
            instance=vm_name,
            instance_resource=vm
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=zone)

        logger.info(f"Firewall rule added to VM '{vm_name}'.")

    def remove_firewall_rule(
            self,
            vm_name: str,
            zone: str,
            security_group_name: str
    ) -> None:
        """Remove Firewall Rule."""
        if not zone:
            zone = self.zone
        # Get the existing VM
        vm = self.get_vm_by_name(vm_name, zone)

        # Remove the firewall rule
        vm.firewall_rules.remove(security_group_name)

        # Update the VM
        operation = self.instance_client.update(
            project=self.credentials.project_id,
            zone=zone,
            instance=vm_name,
            instance_resource=vm
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=zone)

        logger.info(f"Firewall rule removed from VM '{vm_name}'.")

    def add_service_account(
            self,
            vm_name: str,
            zone: str,
            service_account_email: str
    ) -> None:
        """Add Service Account configuration."""
        if not zone:
            zone = self.zone
        # Get the existing VM
        vm = self.get_vm_by_name(vm_name, zone)

        # Add the new service account
        vm.service_accounts.append({
            "email": service_account_email,
            "scopes": ["https://www.googleapis.com/auth/cloud-platform"],
        })

        # Update the VM
        operation = self.instance_client.update(
            project=self.credentials.project_id,
            zone=zone,
            instance=vm_name,
            instance_resource=vm
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=zone)

        logger.info(f"Service account added to VM '{vm_name}'.")

    def remove_service_account(
            self,
            vm_name: str,
            zone: str,
            service_account_email: str
    ) -> None:
        """Remove Service Account configuration."""
        if not zone:
            zone = self.zone
        # Get the existing VM
        vm = self.get_vm_by_name(vm_name, zone)

        # Remove the service account
        for account in vm.service_accounts:
            if account.email == service_account_email:
                vm.service_accounts.remove(account)

        # Update the VM
        operation = self.instance_client.update(
            project=self.credentials.project_id,
            zone=zone,
            instance=vm_name,
            instance_resource=vm
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=zone)

        logger.info(f"Service account removed from VM '{vm_name}'.")

    def add_public_key(self, vm_name: str, zone: str, key: str) -> None:
        """Add Public Key."""
        if not zone:
            zone = self.zone
        # Get the existing VM
        vm = self.get_vm_by_name(vm_name, zone)

        # Add the new public key
        vm.metadata.items.append({"key": "ssh-keys", "value": key})

        # Update the VM
        operation = self.instance_client.update(
            project=self.credentials.project_id,
            zone=zone,
            instance=vm_name,
            instance_resource=vm
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=zone)

        logger.info(f"Public key added to VM '{vm_name}'.")

    def add_public_static_ip(self, vm_name: str, zone: str, ip: str) -> None:
        """Add Public Static IP."""
        if not zone:
            zone = self.zone
        # Get the existing VM
        vm = self.get_vm_by_name(vm_name, zone)

        # Add the new public static IP
        vm.network_interfaces[0].access_configs.append({
            "name": "External NAT",
            "type": "ONE_TO_ONE_NAT",
            "nat_ip": ip,
            "network_tier": "PREMIUM",
        })

        # Update the VM
        operation = self.instance_client.update(
            project=self.credentials.project_id,
            zone=zone,
            instance=vm_name,
            instance_resource=vm
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=zone)

        logger.info(f"Public static IP added to VM '{vm_name}'.")

    def remove_public_static_ip(self, vm_name: str, zone: str, ip: str) -> None:
        """Remove Public Static IP."""
        if not zone:
            zone = self.zone
        # Get the existing VM
        vm = self.get_vm_by_name(vm_name, zone)

        # Remove the public static IP
        for config in vm.network_interfaces[0].access_configs:
            if config.nat_ip == ip:
                vm.network_interfaces[0].access_configs.remove(config)

        # Update the VM
        operation = self.instance_client.update(
            project=self.credentials.project_id,
            zone=zone,
            instance=vm_name,
            instance_resource=vm
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=zone)

        logger.info(f"Public static IP removed from VM '{vm_name}'.")
