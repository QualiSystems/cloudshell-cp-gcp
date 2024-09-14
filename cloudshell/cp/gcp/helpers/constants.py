from __future__ import annotations

import re

SHELL_NAME = "Google GCP Cloud Provider 2G"

VM_FROM_SCRATCH_DEPLOYMENT_PATH = f"{SHELL_NAME}.GCP Instance From Image"
VM_FROM_TEMPLATE_DEPLOYMENT_PATH = f"{SHELL_NAME}.GCP Instance From Template"
VM_FROM_MACHINE_IMAGE_DEPLOYMENT_PATH = f"{SHELL_NAME}.GCP Instance From Machine Image" # noqa E501

SET_WIN_PASSWORD_SCRIPT_TPL = (
    '$Password = ConvertTo-SecureString -String {password} -AsPlainText -Force\n\n'
    'New-LocalUser -name "{user}" -Password $Password\n\n'
    'Add-LocalGroupMember -Group "Administrators" -Member "{user}"'
)

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


DISK_TYPE_MAP = {
    "Standard": "pd-standard",
    "SSD": "pd-ssd",
    "Balanced": "pd-balanced",
    "Extreme": "pd-extreme",
}

