import logging
from functools import cached_property

from google.cloud import compute_v1

from cloudshell.cp.gcp.handlers.base import BaseGCPHandler

logger = logging.getLogger(__name__)


class FirewallPolicyHandler(BaseGCPHandler):
    @cached_property
    def firewall_policy_client(self):
        return compute_v1.FirewallPoliciesClient(credentials=self.credentials)

    def create_firewall_policy(self, policy_name: str, description: str) -> str:
        """Create a new firewall policy."""
        firewall_policy = compute_v1.FirewallPolicy(
            name=policy_name,
            description=description
        )

        operation = self.firewall_policy_client.insert(
            project=self.credentials.project_id, firewall_policy_resource=firewall_policy
        )

        self.wait_for_operation(name=operation.name)

        logger.info(f"Firewall policy '{policy_name}' created successfully.")
        return self.get_firewall_policy_by_name(policy_name).id

    def add_rule_to_firewall_policy(self, policy_id: str, rule: dict) -> None:
        """Add a new rule to an existing firewall policy."""
        firewall_rule = compute_v1.FirewallPolicyRule(
            priority=rule['priority'],
            action=rule['action'],
            match=compute_v1.FirewallPolicyRuleMatcher(
                layer4_configs=[
                    compute_v1.FirewallPolicyRuleMatcherLayer4Config(
                        ip_protocol=rule['ip_protocol'],
                        ports=rule['ports']
                    )
                ]
            ),
            direction=rule['direction']
        )

        operation = self.firewall_policy_client.add_rule(
            firewall_policy=policy_id,
            firewall_policy_rule_resource=firewall_rule
        )

        self.wait_for_operation(name=operation.name)

        logger.info(f"Rule added to firewall policy '{policy_id}'.")

    def get_firewall_policy_by_name(self, policy_name: str) -> compute_v1.FirewallPolicy:
        """Get firewall policy instance by its name."""
        return self.firewall_policy_client.get(
            project=self.credentials.project_id, firewall_policy=policy_name
        )
