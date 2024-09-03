from __future__ import annotations

from .base_flow import AbstractGCPDeployFlow
from .from_scratch import GCPDeployInstanceFromScratchFlow
from .from_template import GCPDeployInstanceFromTemplateFlow
from .from_image import GCPDeployInstanceFromImageFlow

from cloudshell.cp.gcp.models import deploy_app

DEPLOY_APP_TO_FLOW_PARAMS = (
    (deploy_app.InstanceFromScratchDeployApp, GCPDeployInstanceFromScratchFlow),
    (deploy_app.InstanceFromTemplateDeployApp, GCPDeployInstanceFromTemplateFlow),
    (deploy_app.InstanceFromMachineImageDeployApp, GCPDeployInstanceFromImageFlow),
)


def get_deploy_params(request_action) -> type[AbstractGCPDeployFlow]:
    da = request_action.deploy_app
    for deploy_class, deploy_params in DEPLOY_APP_TO_FLOW_PARAMS:
        if isinstance(da, deploy_class):
            return deploy_params
    raise NotImplementedError(f"Not supported deployment type {type(da)}")


__all__ = (
    GCPDeployInstanceFromScratchFlow,
    GCPDeployInstanceFromTemplateFlow,
    GCPDeployInstanceFromImageFlow,
    get_deploy_params,
)
