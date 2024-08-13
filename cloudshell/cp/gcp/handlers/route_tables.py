from __future__ import annotations

import logging

from google.cloud import compute_v1
from functools import cached_property

from cloudshell.cp.gcp.handlers.base import BaseGCPHandler


logger = logging.getLogger(__name__)


class RouteTablesHandler(BaseGCPHandler):
    @cached_property
    def route_table_client(self):
        return compute_v1.RoutesClient(credentials=self.credentials)

    def create(self, route_table_name, network_name, tags, next_hop_instance=None, next_hop_ip=None):
        # Define the route table settings
        route_table = compute_v1.Route()
        route_table.name = route_table_name
        route_table.network = f"projects/{self.project_id}/global/networks/{network_name}"
        route_table.tags = tags
        # route_table.dest_range = ""
        # route_table.priority = 1000
        # route_table.next_hop_instance = next_hop_instance
        # route_table.next_hop_ip = next_hop_ip
        
        # Create the route table
        operation = self.route_table_client.insert(
            project=self.project_id,
            route_resource=route_table
        )
        
        # Wait for the operation to complete
        operation_client = compute_v1.GlobalOperationsClient()
        operation_client.wait(project=self.project_id, operation=operation.name)
        
        logger.info(f"Route table '{route_table_name}' created successfully.")
        
    def get_route_table_by_name(self, route_table_name):
        logger.info("Getting route table")
        return self.route_table_client.get(project=self.project_id, route=route_table_name)
    
    def delete(self, route_table_name):
        operation = self.route_table_client.delete(project=self.project_id, route=route_table_name)

        # Wait for the operation to complete
        operation_client = compute_v1.GlobalOperationsClient()
        operation_client.wait(project=self.project_id, operation=operation.name)

        logger.info(f"Route table '{route_table_name}' deleted successfully.")
        
    def add_rule(self, route_table_name, dst_range, priority=1000, tags=dict,
                 next_hop_instance=None,
                 next_hop_ip=None):
        # Get the existing route table
        route_table = self.get_route_table_by_name(route_table_name)
        
        # Add the new rule
        new_rule = compute_v1.Route()
        new_rule.name = route_table_name
        new_rule.network = route_table.network
        new_rule.tags = tags
        new_rule.dest_range = dst_range
        new_rule.priority = priority
        new_rule.next_hop_instance = next_hop_instance
        new_rule.next_hop_ip = next_hop_ip
        
        route_table.append(new_rule)
        
        # Update the route table
        operation = self.route_table_client.insert(
            project=self.project_id,
            route_resource=route_table
        )
        
        # Wait for the operation to complete
        operation_client = compute_v1.GlobalOperationsClient()
        operation_client.wait(project=self.project_id, operation=operation.name)
        
        logger.info(f"Rule added to route table '{route_table_name}' successfully.")
