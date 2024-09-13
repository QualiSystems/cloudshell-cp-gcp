from __future__ import annotations

from cloudshell.cp.core.request_actions import (
    DeployedVMActions,
    GetVMDetailsRequestActions,
)
from cloudshell.cp.core.request_actions.models import DeployedApp

from cloudshell.cp.gcp.helpers import constants
from cloudshell.cp.gcp.models.attributes import (
    ResourceAttrRODeploymentPath,
    ResourceBoolAttrRODeploymentPath,
    ResourceIntAttrRODeploymentPath,
    BaseGCPDeploymentAppAttributeNames,
    GCPFromScratchDeploymentAppAttributeNames,
    GCPFromTemplateDeploymentAppAttributeNames,
    GCPFromVMImageDeploymentAppAttributeNames,
)


class BaseGCPDeployedApp(DeployedApp):
    ATTR_NAMES = BaseGCPDeploymentAppAttributeNames

    region = ResourceAttrRODeploymentPath(ATTR_NAMES.region)
    zone = ResourceAttrRODeploymentPath(ATTR_NAMES.zone)
    machine_type = ResourceAttrRODeploymentPath(ATTR_NAMES.machine_type)
    maintenance = ResourceAttrRODeploymentPath(ATTR_NAMES.maintenance)
    auto_restart = ResourceBoolAttrRODeploymentPath(ATTR_NAMES.auto_restart)
    ip_forwarding = ResourceBoolAttrRODeploymentPath(ATTR_NAMES.ip_forwarding)
    # network = ResourceAttrRODeploymentPath(ATTR_NAMES.network)
    # sub_network = ResourceAttrRODeploymentPath(ATTR_NAMES.sub_network)
    inbound_ports = ResourceAttrRODeploymentPath(ATTR_NAMES.inbound_ports)
    custom_tags = ResourceAttrRODeploymentPath(ATTR_NAMES.custom_tags)
    wait_for_ip = ResourceBoolAttrRODeploymentPath(ATTR_NAMES.wait_for_ip)
    add_public_ip = ResourceBoolAttrRODeploymentPath(ATTR_NAMES.add_public_ip)
    autoload = ResourceBoolAttrRODeploymentPath(ATTR_NAMES.autoload)
    autogenerated_name = ResourceBoolAttrRODeploymentPath(ATTR_NAMES.autogenerated_name)


class InstanceFromScratchDeployedApp(BaseGCPDeployedApp):
    ATTR_NAMES = GCPFromScratchDeploymentAppAttributeNames

    DEPLOYMENT_PATH = constants.VM_FROM_SCRATCH_DEPLOYMENT_PATH

    # disk_image_type = ResourceAttrRODeploymentPath(ATTR_NAMES.disk_image_type)
    disk_type = ResourceAttrRODeploymentPath(ATTR_NAMES.disk_type)
    disk_size = ResourceIntAttrRODeploymentPath(ATTR_NAMES.disk_size)
    disk_rule = ResourceAttrRODeploymentPath(ATTR_NAMES.disk_rule)
    project_cloud = ResourceAttrRODeploymentPath(ATTR_NAMES.project_cloud)
    disk_image = ResourceAttrRODeploymentPath(ATTR_NAMES.disk_image)


class InstanceFromTemplateDeployedApp(InstanceFromScratchDeployedApp):
    ATTR_NAMES = GCPFromTemplateDeploymentAppAttributeNames

    DEPLOYMENT_PATH = constants.VM_FROM_TEMPLATE_DEPLOYMENT_PATH
    template_name = ResourceAttrRODeploymentPath(ATTR_NAMES.template_name)


class InstanceFromMachineImageDeployedApp(BaseGCPDeployedApp):
    ATTR_NAMES = GCPFromVMImageDeploymentAppAttributeNames

    DEPLOYMENT_PATH = constants.VM_FROM_MACHINE_IMAGE_DEPLOYMENT_PATH
    machine_image = ResourceAttrRODeploymentPath(ATTR_NAMES.machine_image)


class GCPGetVMDetailsRequestActions(GetVMDetailsRequestActions):
    deployed_app: BaseGCPDeployedApp


class GCPDeployedVMRequestActions(DeployedVMActions):
    deploy_app: BaseGCPDeployedApp
