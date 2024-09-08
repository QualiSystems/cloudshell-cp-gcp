from __future__ import annotations

import re

SHELL_NAME = "Google Cloud Provider Shell 2G"

VM_FROM_SCRATCH_DEPLOYMENT_PATH = f"{SHELL_NAME}.Google Cloud Instance From Scratch"
VM_FROM_TEMPLATE_DEPLOYMENT_PATH = f"{SHELL_NAME}.Google Cloud Instance From Template"
VM_FROM_MACHINE_IMAGE_DEPLOYMENT_PATH = f"{SHELL_NAME}.Google Cloud Instance From Machine Image" # noqa E501

TAG_KEY_PATTERN = re.compile(r"[^a-z0-9-_]")

# gcloud compute images list result:
PUBLIC_IMAGE_PROJECTS = {
    "CenOS":                            "centos-cloud",
    "Container Optimized OS":           "cos-cloud",
    "Debian":                           "debian-cloud",
    "Deep Learning on Linux":           "ml-images",
    "Fedora CoreOS":                    "fedora-coreos-cloud",
    "HPC VM Image":                     "cloud-hpc-image-public",
    "openSUSE":                         "opensuse-cloud",
    "Red Hat Enterprise Linux":         "rhel-cloud",
    "Red Hat Enterprise Linux for SAP": "rhel-sap-cloud",
    "Rocky Linux":                      "rocky-linux-cloud",
    "SQL Server on Windows Server":     "windows-sql-cloud",
    "SUSE Linux Enterprise BYOS":       "suse-byos-cloud",
    "SUSE Linux Enterprise Server":     "suse-cloud",
    "SUSE Linux Enterprise for SAP":    "suse-sap-cloud",
    "Ubuntu":                           "ubuntu-os-cloud",
    "Ubuntu Pro":                       "ubuntu-os-pro-cloud",
    "Windows Server":                   "windows-cloud",
}
