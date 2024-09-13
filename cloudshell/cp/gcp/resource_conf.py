from __future__ import annotations

from collections.abc import Callable
from functools import cached_property
from typing import TYPE_CHECKING

from attr import Attribute, define
from typing_extensions import Self

from cloudshell.api.cloudshell_api import CloudShellAPISession, ResourceInfo
from cloudshell.cp.core.reservation_info import ReservationInfo

from cloudshell.shell.core.driver_context import ResourceRemoteCommandContext
from cloudshell.shell.standards.core.namespace_type import NameSpaceType
from cloudshell.shell.standards.core.resource_conf import BaseConfig, attr
from cloudshell.shell.standards.core.resource_conf.attrs_getter import (
    MODEL,
    RESOURCE_CONTEXT_TYPES,
    AbsAttrsGetter,
)
from cloudshell.shell.standards.core.resource_conf.base_conf import password_decryptor
from cloudshell.shell.standards.core.resource_conf.resource_attr import AttrMeta

from cloudshell.cp.gcp.helpers.converters import get_credentials, get_custom_tags

if TYPE_CHECKING:
    from google.auth.credentials import Credentials


class ResourceInfoAttrGetter(AbsAttrsGetter):
    def __init__(
        self,
        model_cls: type[MODEL],
        decrypt_password: Callable[[str], str],
        details: ResourceInfo,
    ):
        super().__init__(model_cls, decrypt_password)
        self.details = details
        self._attrs = {a.Name: a.Value for a in details.ResourceAttributes}
        self.shell_name = details.ResourceModelName
        self.family_name = details.ResourceFamilyName

    def _extract_attr_val(self, f: Attribute, meta: AttrMeta) -> str:
        key = self._get_key(meta)
        return self._attrs[key]

    def _get_key(self, meta: AttrMeta) -> str:
        namespace = self._get_namespace(meta.namespace_type)
        return f"{namespace}.{meta.name}"

    def _get_namespace(self, namespace_type: NameSpaceType) -> str:
        if namespace_type is NameSpaceType.SHELL_NAME:
            namespace = self.shell_name
        elif namespace_type is NameSpaceType.FAMILY_NAME:
            namespace = self.family_name
        else:
            raise ValueError(f"Unknown namespace: {namespace_type}")
        return namespace


class GCPAttributeNames:
    region = "Region"
    json_keys = "Credentials Json"
    zone = "Availability Zone"
    keypairs_location = "Keypairs Location"
    additional_mgmt_networks = "Additional Mgmt Networks"
    machine_type = "Machine Type"
    custom_tags = "Custom Tags"
    networks_in_use = "Networks in use"


@define(slots=False, str=False)
class GCPResourceConfig(BaseConfig):
    context: RESOURCE_CONTEXT_TYPES
    ATTR_NAMES = GCPAttributeNames

    region: str = attr(ATTR_NAMES.region)
    machine_type: str = attr(ATTR_NAMES.machine_type)
    networks_in_use: str = attr(ATTR_NAMES.networks_in_use)
    keypairs_location: str = attr(ATTR_NAMES.keypairs_location)
    additional_mgmt_networks: list = attr(ATTR_NAMES.additional_mgmt_networks,
                                          default="")
    credentials: Credentials = attr(
        ATTR_NAMES.json_keys, is_password=True, converter=get_credentials
    )
    custom_tags: dict = attr(
        ATTR_NAMES.custom_tags,
        default="",
        converter=get_custom_tags
    )
    # availability_zone: str = attr(ATTR_NAMES.zone)

    @cached_property
    def reservation_info(self) -> ReservationInfo:
        if isinstance(self.context, ResourceRemoteCommandContext):
            return ReservationInfo.from_remote_resource_context(self.context)
        return ReservationInfo.from_resource_context(self.context)

    @cached_property
    def tags(self) -> dict:
        default_tags = self._generate_default_tags()
        return {**default_tags, **self.custom_tags}

    def _generate_default_tags(self):
        return {
            "Created_By": "Quali",
            "Blueprint": self.reservation_info.blueprint,
            "Owner": self.reservation_info.owner,
            "Domain": self.reservation_info.domain,
            "Sandbox_Id": self.reservation_info.reservation_id,
        }

    @classmethod
    def from_context(
        cls, context: RESOURCE_CONTEXT_TYPES, api: CloudShellAPISession
    ) -> Self:
        attrs = cls._ATTR_GETTER(cls, password_decryptor(api), context).get_attrs()
        converter = cls._CONVERTER(cls, attrs)

        return cls(
            name=context.resource.name,
            shell_name=context.resource.model,
            family_name=context.resource.family,
            address=context.resource.address,
            api=api,
            context=context,
            # this should return kwargs but BaseConfig doesn't have any
            **converter.convert(),  # noqa
        )

    @classmethod
    def from_cs_resource_details(
        cls,
        details: ResourceInfo,
        api: CloudShellAPISession,
    ) -> GCPResourceConfig:
        attrs = ResourceInfoAttrGetter(
            cls, password_decryptor(api), details
        ).get_attrs()
        converter = cls._CONVERTER(cls, attrs)
        return cls(
            name=details.Name,
            shell_name=details.ResourceModelName,
            family_name=details.ResourceFamilyName,
            address=details.Address,
            api=api,
            **converter.convert(),
        )
