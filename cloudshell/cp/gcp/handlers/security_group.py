from __future__ import annotations

import logging

from google.cloud import compute_v1
from functools import cached_property
from typing import TYPE_CHECKING

from cloudshell.cp.gcp.handlers.base import BaseGCPHandler


# if TYPE_CHECKING:

logger = logging.getLogger(__name__)


class SecurityGroupHandler(BaseGCPHandler):
    @cached_property
    def firewall_client(self):
        return compute_v1.FirewallsClient(credentials=self.credentials)

    def create(self, security_group_name, network_name, rules):
        # Define the firewall settings
        firewall = compute_v1.Firewall()
        firewall.name = security_group_name
        firewall.network = f"projects/{self.project_id}/global/networks/{network_name}"
        firewall.allowed = rules

        # Create the firewall
        operation = self.firewall_client.insert(
            project=self.project_id,
            firewall_resource=firewall
        )

        # Wait for the operation to complete
        operation_client = compute_v1.GlobalOperationsClient()
        operation_client.wait(project=self.project_id, operation=operation.name)

        print(f"Security group '{security_group_name}' created successfully.")

    def get_security_group_by_name(self, security_group_name):
        logger.info("Getting security group")
        return self.firewall_client.get(project=self.project_id, firewall=security_group_name)

    def delete(self, security_group_name):
        operation = self.firewall_client.delete(project=self.project_id, firewall=security_group_name)

        # Wait for the operation to complete
        operation_client = compute_v1.GlobalOperationsClient()
        operation_client.wait(project=self.project_id, operation=operation.name)

        print(f"Security group '{security_group_name}' deleted successfully.")

    def add_rule(self, security_group_name, rule):
        # Get the existing firewall
        firewall = self.get_security_group_by_name(security_group_name)

        # Add the new rule
        firewall.allowed.append(rule)

        # Update the firewall
        operation = self.firewall_client.update(
            project=self.project_id,
            firewall=security_group_name,
            firewall_resource=firewall
        )

        # Wait for the operation to complete
        operation_client = compute_v1.GlobalOperationsClient()
        operation_client.wait(project=self.project_id, operation=operation.name)

        print(f"Rule '{rule}' added to security group '{security_group_name}'.")
