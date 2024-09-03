from __future__ import annotations

import logging
import random
from functools import cached_property
from typing import TYPE_CHECKING

from attrs import define
from google.cloud import compute_v1

from cloudshell.cp.gcp.handlers.base import BaseGCPHandler
from cloudshell.cp.gcp.helpers.errors import AttributeGCPError

if TYPE_CHECKING:
    from google.cloud.compute_v1.types import compute

logger = logging.getLogger(__name__)


@define
class InstanceHandler(BaseGCPHandler):
    zone: str
    region: str | None = None

    @cached_property
    def instance_client(self):
        return compute_v1.InstancesClient(credentials=self.credentials)

    def zone_checker(self):
        def decorator(func):
            def wrapper(*args, **kwargs):
                if not kwargs.get("zone"):
                    if self.zone:
                        kwargs.update({"zone": self.zone})
                    else:
                        if self.region:
                            zones = self.get_zones(region=self.region)
                            zone = random.choice(zones)
                            kwargs.update({"zone": zone.name})
                        else:
                            raise AttributeGCPError("Zone cannot be empty.")
                operation = func(*args, **kwargs)
                return operation
            return wrapper
        return decorator

    @zone_checker()
    def deploy(self, instance: compute.Instance, *, zone: str | None = None) -> int:
        """Create Virtual Machine."""
        operation = self.instance_client.insert(
            project=self.credentials.project_id,
            zone=zone,
            instance_resource=instance
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=zone)

        logger.info(f"VM '{instance.name}' created successfully.")
        return instance.name
        # return self.get_vm_by_name(vm_name=instance.name, zone=zone).id

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

    @zone_checker()
    def get_vm_by_name(self, instance_name: str, *, zone: str) -> compute.Instance:
        """Get VM instance by its name."""
        logger.info("Getting VM")
        return self.instance_client.get(
            project=self.credentials.project_id, zone=zone, instance=instance_name
        )

    @zone_checker()
    def get_vms_by_tag_value(
        self,
        tag: str,
        tag_value: str,
        *,
        zone: str
    ) -> list[compute.Instance]:
        """Get Virtual Machine instances by tag."""
        logger.info("Getting VMs by tag")
        vms = self.instance_client.list(project=self.credentials.project_id, zone=zone)

        # Filter VMs by tag value
        return [vm for vm in vms if tag_value in vm.tags.get(tag)]

    @zone_checker()
    def get_vm_by_id(self, vm_id: str, *, zone: str) -> compute.Instance:
        """Get Virtual Machine instance by its ID."""
        logger.info("Getting VM by VM ID")
        return self.instance_client.get(
            project=self.credentials.project_id, zone=zone, instance=vm_id
        )

    @zone_checker()
    def delete(self, vm_name: str, *, zone: str) -> None:
        """Delete Virtual Machine instance."""
        operation = self.instance_client.delete(
            project=self.credentials.project_id, zone=zone, instance=vm_name
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=zone)

        logger.info(f"VM '{vm_name}' deleted successfully.")

    @zone_checker()
    def start(self, vm_name: str, *, zone: str) -> None:
        """Power On Virtual Machine."""
        operation = self.instance_client.start(
            project=self.credentials.project_id, zone=zone, instance=vm_name
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=zone)

        logger.info(f"VM '{vm_name}' started successfully.")

    @zone_checker()
    def stop(self, vm_name: str, *, zone: str) -> None:
        """Power Off Virtual Machine."""
        operation = self.instance_client.stop(
            project=self.credentials.project_id, zone=zone, instance=vm_name
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=zone)

        logger.info(f"VM '{vm_name}' stopped successfully.")

    @zone_checker()
    def add_tag(self, vm_name: str, tag: dict[str, str], *, zone: str) -> None:
        """Add tag to existed Virtual Machine."""
        # Get the existing VM
        vm = self.get_vm_by_name(vm_name, zone)

        # Add the new tag
        vm.tags.append(tag)

        # Update the VM
        operation = self.instance_client.update(
            project=self.credentials.project_id,
            zone=zone,
            instance=vm_name,
            instance_resource=vm,
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=zone)

        logger.info(f"Tag '{tag}' added to VM '{vm_name}'.")

    @zone_checker()
    def remove_tag(self, vm_name: str, tag: str, *, zone: str) -> None:
        """Remove tag."""
        # Get the existing VM
        vm = self.get_vm_by_name(vm_name, zone)

        # Remove the tag
        vm.tags.remove(tag)

        # Update the VM
        operation = self.instance_client.update(
            project=self.credentials.project_id,
            zone=zone,
            instance=vm_name,
            instance_resource=vm,
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=zone)

        logger.info(f"Tag '{tag}' removed from VM '{vm_name}'.")

    @zone_checker()
    def add_metadata(self, vm_name: str, key: str, value: str, *, zone: str) -> None:
        """Add metadata record."""
        # Get the existing VM
        vm = self.get_vm_by_name(vm_name, zone)

        # Add the new metadata
        vm.metadata.items.append({"key": key, "value": value})

        # Update the VM
        operation = self.instance_client.update(
            project=self.credentials.project_id,
            zone=zone,
            instance=vm_name,
            instance_resource=vm,
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=zone)

        logger.info(f"Metadata '{key}={value}' added to VM '{vm_name}'.")

    @zone_checker()
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
            zone=zone,
            instance=vm_name,
            instance_resource=vm,
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=zone)

        logger.info(f"Metadata '{key}' removed from VM '{vm_name}'.")

    @zone_checker()
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
            zone=zone,
            instance=vm_name,
            instance_resource=vm,
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=zone)

        logger.info(f"Network interface added to VM '{vm_name}'.")

    @zone_checker()
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
            zone=zone,
            instance=vm_name,
            instance_resource=vm,
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=zone)

        logger.info(f"Network interface removed from VM '{vm_name}'.")

    @zone_checker()
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
            zone=zone,
            instance=vm_name,
            instance_resource=vm,
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=zone)

        logger.info(f"Disk '{disk_name}' added to VM '{vm_name}'.")

    @zone_checker()
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
            zone=zone,
            instance=vm_name,
            instance_resource=vm,
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=zone)

        logger.info(f"Disk '{disk_name}' removed from VM '{vm_name}'.")

    @zone_checker()
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
            zone=zone,
            instance=vm_name,
            instance_resource=vm,
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=zone)

        logger.info(f"Access config added to VM '{vm_name}'.")

    @zone_checker()
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
            zone=zone,
            instance=vm_name,
            instance_resource=vm,
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=zone)

        logger.info(f"Access config removed from VM '{vm_name}'.")

    @zone_checker()
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
            zone=zone,
            instance=vm_name,
            instance_resource=vm,
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=zone)

        logger.info(f"Firewall rule added to VM '{vm_name}'.")

    @zone_checker()
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
            zone=zone,
            instance=vm_name,
            instance_resource=vm,
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=zone)

        logger.info(f"Firewall rule removed from VM '{vm_name}'.")

    @zone_checker()
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
            zone=zone,
            instance=vm_name,
            instance_resource=vm,
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=zone)

        logger.info(f"Service account added to VM '{vm_name}'.")

    @zone_checker()
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
            zone=zone,
            instance=vm_name,
            instance_resource=vm,
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=zone)

        logger.info(f"Service account removed from VM '{vm_name}'.")

    @zone_checker()
    def add_public_key(self, vm_name: str, key: str, *, zone: str) -> None:
        """Add Public Key."""
        # Get the existing VM
        vm = self.get_vm_by_name(vm_name, zone)

        # Add the new public key
        vm.metadata.items.append({"key": "ssh-keys", "value": key})

        # Update the VM
        operation = self.instance_client.update(
            project=self.credentials.project_id,
            zone=zone,
            instance=vm_name,
            instance_resource=vm,
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=zone)

        logger.info(f"Public key added to VM '{vm_name}'.")

    @zone_checker()
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
            zone=zone,
            instance=vm_name,
            instance_resource=vm,
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=zone)

        logger.info(f"Public static IP added to VM '{vm_name}'.")

    @zone_checker()
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
            zone=zone,
            instance=vm_name,
            instance_resource=vm,
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name, zone=zone)

        logger.info(f"Public static IP removed from VM '{vm_name}'.")
