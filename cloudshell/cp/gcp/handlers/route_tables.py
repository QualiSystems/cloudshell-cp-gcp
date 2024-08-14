from __future__ import annotations

import logging

from google.cloud import compute_v1
from functools import cached_property
from typing_extensions import TYPE_CHECKING

from cloudshell.cp.gcp.handlers.base import BaseGCPHandler

if TYPE_CHECKING:
    from google.cloud.compute_v1.types import compute

logger = logging.getLogger(__name__)


class RouteTablesHandler(BaseGCPHandler):
    @cached_property
    def route_table_client(self):
        return compute_v1.RoutesClient(credentials=self.credentials)

    def create(
            self,
            route_table_name: str,
            network_name: str,
            tags,
            next_hop_instance=None,
            next_hop_ip=None
    ) -> str:
        """Create Route Table."""
        # Define the route table settings
        route_table = compute_v1.Route()
        route_table.name = route_table_name
        route_table.network = f"projects/{self.credentials.project_id}/global/networks/{network_name}"
        route_table.tags = tags
        # route_table.dest_range = ""
        # route_table.priority = 1000
        # route_table.next_hop_instance = next_hop_instance
        # route_table.next_hop_ip = next_hop_ip
        
        # Create the route table
        operation = self.route_table_client.insert(
            project=self.credentials.project_id,
            route_resource=route_table
        )
        
        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name)
        
        logger.info(f"Route table '{route_table_name}' created successfully.")
        return self.get_route_table_by_name(route_table_name).id
        
    def get_route_table_by_name(self, route_table_name: str) -> compute.Route:
        """Get Route Table instance by it name."""
        logger.info("Getting route table")
        return self.route_table_client.get(project=self.credentials.project_id, route=route_table_name)
    
    def delete(self, route_table_name):
        """Delete Route Table."""
        operation = self.route_table_client.delete(
            project=self.credentials.project_id,
            route=route_table_name
        )

        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name)

        logger.info(f"Route table '{route_table_name}' deleted successfully.")
        
    def add_rule(
            self,
            route_table_name: str,
            dst_range: str,
            priority: int = 1000,
            tags: dict = None,
            next_hop_instance=None,
            next_hop_ip=None
    ):
        """Add single rule to existed Route Table."""
        # Get the existing route table
        route_table = self.get_route_table_by_name(route_table_name)
        
        # Add the new rule
        new_rule = compute_v1.Route()
        new_rule.name = route_table_name
        new_rule.network = route_table.network
        new_rule.tags = tags or {}
        new_rule.dest_range = dst_range
        new_rule.priority = priority
        new_rule.next_hop_instance = next_hop_instance
        new_rule.next_hop_ip = next_hop_ip
        
        route_table.append(new_rule)
        
        # Update the route table
        operation = self.route_table_client.insert(
            project=self.credentials.project_id,
            route_resource=route_table
        )
        
        # Wait for the operation to complete
        self.wait_for_operation(name=operation.name)
        
        logger.info(f"Rule added to route table '{route_table_name}' successfully.")
