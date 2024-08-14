from cloudshell.cp.core.flows.prepare_sandbox_infra import AbstractPrepareSandboxInfraFlow
from cloudshell.cp.core.request_actions import PrepareSandboxInfraRequestActions as actions
from cloudshell.cp.core.utils import generate_ssh_key_pair

from cloudshell.cp.gcp.handlers.ssh_keys import SSHKeysHandler
from cloudshell.cp.gcp.handlers.subnet import SubnetHandler
from cloudshell.cp.gcp.handlers.vpc import VPCHandler


class PrepareGCPInfraFlow(AbstractPrepareSandboxInfraFlow):
    def prepare_cloud_infra(self, request_actions: actions):
        # create vpc using vpc handler
        vpc_handler = VPCHandler.from_config(self.config)
        vpc_handler.create(request_actions.vpc_name)
        return vpc_handler.get_vpc_by_name(request_actions.vpc_name).id

    def prepare_subnets(self, request_actions: actions):
        # create subnets using subnet handler
        subnet_handler = SubnetHandler.from_config(self.config)
        for subnet_request in request_actions.prepare_subnets:
            subnet_handler.create(subnet_request.cidr, subnet_request.name)

    def create_ssh_keys(self, request_actions: actions):
        private_key, public_key = generate_ssh_key_pair()
        ssh_keys_handler = SSHKeysHandler.from_config(self.config)
        ssh_keys_handler.upload_ssh_keys(
            bucket_name=self.config.ssh_keys_bucket_name,
            folder_path=self.config.sandbox_id,
            file_path=private_key
        )
        ssh_keys_handler.upload_ssh_keys(
            bucket_name=self.config.ssh_keys_bucket_name,
            folder_path=self.config.sandbox_id,
            file_path=public_key
        )
        return private_key

    def prepare_common_objects(self, request_actions: actions):
        pass