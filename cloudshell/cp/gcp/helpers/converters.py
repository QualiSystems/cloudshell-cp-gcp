from __future__ import annotations

import json
from contextlib import suppress
from typing import TYPE_CHECKING

from google.oauth2 import service_account
from google.auth import default, exceptions

from cloudshell.cp.gcp.helpers.errors import AttributeGCPError

if TYPE_CHECKING:
    from google.auth.credentials import Credentials


def get_credentials(account_info: str) -> Credentials:
    """Get Account Credentials."""
    if not account_info:
        # Try to get default credentials. Can be used when CS deployed in GCP
        with suppress(exceptions.DefaultCredentialsError):
            return default()
    else:
        # Assume that json data provided
        with suppress(AttributeError):
            account_dict = json.loads(account_info)
            return service_account.Credentials.from_service_account_info(account_dict)

        # Otherwise, the path to the configuration file is expected
        with suppress(FileNotFoundError):
            return service_account.Credentials.from_service_account_file(account_info)

    raise AttributeGCPError("Cannot get service account information.")
