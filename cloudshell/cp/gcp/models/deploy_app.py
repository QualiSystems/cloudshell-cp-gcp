from __future__ import annotations

from cloudshell.cp.core.request_actions import DeployVMRequestActions
from cloudshell.cp.core.request_actions.models import DeployApp

from cloudshell.cp.gcp.helpers import constants
from cloudshell.cp.gcp.helpers.constants import DISK_TYPE_MAP, PUBLIC_IMAGE_PROJECTS
from cloudshell.cp.gcp.helpers.network_tag_helper import parse_port_range
from cloudshell.cp.gcp.helpers.password_generator import generate_password
from cloudshell.cp.gcp.models.attributes import (
    ResourceAttrRODeploymentPath,
    ResourceBoolAttrRODeploymentPath,
    ResourceIntAttrRODeploymentPath,
    BaseGCPDeploymentAppAttributeNames,
    GCPFromScratchDeploymentAppAttributeNames,
    GCPFromTemplateDeploymentAppAttributeNames,
    GCPFromVMImageDeploymentAppAttributeNames,
)

class CustomTagsAttrRO(ResourceAttrRODeploymentPath):
    def __get__(self, instance, owner):
        if instance is None:
            return self

        attr = instance.attributes.get(self.get_key(instance), self.default)
        if attr:
            try:
                return {
                    tag_key.strip(): tag_val.strip()
                    for tag_key, tag_val in [
                        tag_data.split("=") for tag_data in attr.split(";") if tag_data
                    ]
                }
            except ValueError:
                raise Exception(
                    "'Custom Tags' attribute is in incorrect format"
                )

        return {}


class InboundPortsAttrRO(ResourceAttrRODeploymentPath):
    def __get__(self, instance, owner):
        if instance is None:
            return self

        attr = instance.attributes.get(self.get_key(instance), self.default)
        return [parse_port_range(port_data.strip()) for port_data in attr.split(";")
                if port_data]


class OnOffBoolAttrRO(ResourceBoolAttrRODeploymentPath):
    TRUE_VALUES = {"on", "yes", "y"}
    FALSE_VALUES = {"off", "no", "n"}


class DiskTypeAttrRO(ResourceBoolAttrRODeploymentPath):
    def __get__(self, instance, owner):
        if instance is None:
            return self

        attr = instance.attributes.get(self.get_key(instance), self.default)
        return DISK_TYPE_MAP.get(attr, "")


class ImageProjectAttrRO(ResourceAttrRODeploymentPath):
    def __get__(self, instance, owner):
        if instance is None:
            return self

        attr = instance.attributes.get(self.get_key(instance), self.default)
        return PUBLIC_IMAGE_PROJECTS.get(attr, attr)


class BaseGCPDeployApp(DeployApp):
    _DO_NOT_EDIT_APP_NAME = True
    ATTR_NAMES = BaseGCPDeploymentAppAttributeNames

    region = ResourceAttrRODeploymentPath(ATTR_NAMES.region)
    zone = ResourceAttrRODeploymentPath(ATTR_NAMES.zone)
    machine_type = ResourceAttrRODeploymentPath(ATTR_NAMES.machine_type)
    maintenance = ResourceAttrRODeploymentPath(ATTR_NAMES.maintenance)
    ip_regex = ResourceAttrRODeploymentPath(ATTR_NAMES.ip_regex)
    refresh_ip_timeout = ResourceIntAttrRODeploymentPath(ATTR_NAMES.refresh_ip_timeout)
    auto_restart = OnOffBoolAttrRO(ATTR_NAMES.auto_restart)
    ip_forwarding = ResourceBoolAttrRODeploymentPath(ATTR_NAMES.ip_forwarding)
    inbound_ports = InboundPortsAttrRO(ATTR_NAMES.inbound_ports)
    custom_tags = CustomTagsAttrRO(ATTR_NAMES.custom_tags)
    wait_for_ip = ResourceBoolAttrRODeploymentPath(ATTR_NAMES.wait_for_ip)
    add_public_ip = ResourceBoolAttrRODeploymentPath(ATTR_NAMES.add_public_ip)
    autoload = ResourceBoolAttrRODeploymentPath(ATTR_NAMES.autoload)
    autogenerated_name = ResourceBoolAttrRODeploymentPath(ATTR_NAMES.autogenerated_name)

    @property
    def user(self):
        return super().user or "admin"


class InstanceFromScratchDeployApp(BaseGCPDeployApp):
    ATTR_NAMES = GCPFromScratchDeploymentAppAttributeNames

    DEPLOYMENT_PATH = constants.VM_FROM_SCRATCH_DEPLOYMENT_PATH

    # disk_image_type = ResourceAttrRODeploymentPath(ATTR_NAMES.disk_image_type)
    disk_type = DiskTypeAttrRO(ATTR_NAMES.disk_type)
    disk_size = ResourceIntAttrRODeploymentPath(ATTR_NAMES.disk_size)
    # disk_rule = ResourceAttrRODeploymentPath(ATTR_NAMES.disk_rule)
    disk_rule = True
    project_cloud = ImageProjectAttrRO(ATTR_NAMES.project_cloud)
    disk_image = ResourceAttrRODeploymentPath(ATTR_NAMES.disk_image)

    @property
    def password(self):
        result = super().password
        if not result and "windows" in self.project_cloud:
           result = generate_password()
        return result


class InstanceFromTemplateDeployApp(InstanceFromScratchDeployApp):
    ATTR_NAMES = GCPFromTemplateDeploymentAppAttributeNames

    DEPLOYMENT_PATH = constants.VM_FROM_TEMPLATE_DEPLOYMENT_PATH
    template_name = ResourceAttrRODeploymentPath(ATTR_NAMES.template_name)
    auto_restart = ResourceAttrRODeploymentPath(ATTR_NAMES.auto_restart)


class InstanceFromMachineImageDeployApp(BaseGCPDeployApp):
    ATTR_NAMES = GCPFromVMImageDeploymentAppAttributeNames

    DEPLOYMENT_PATH = constants.VM_FROM_MACHINE_IMAGE_DEPLOYMENT_PATH
    machine_image = ResourceAttrRODeploymentPath(ATTR_NAMES.machine_image)


class GCPDeployVMRequestActions(DeployVMRequestActions):
    deploy_app: BaseGCPDeployApp
