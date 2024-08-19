from __future__ import annotations

from functools import cached_property

from attr import define, Attribute
from collections.abc import Callable

from cloudshell.cp.core.reservation_info import ReservationInfo
from cloudshell.helpers.scripts.cloudshell_scripts_helpers import \
    ReservationContextDetails
from cloudshell.shell.core.driver_context import ResourceRemoteCommandContext
from typing_extensions import Self
from typing_extensions import TYPE_CHECKING

from cloudshell.api.cloudshell_api import ResourceInfo, CloudShellAPISession
from cloudshell.shell.standards.core.namespace_type import NameSpaceType
from cloudshell.shell.standards.core.resource_conf import attr, BaseConfig
from cloudshell.shell.standards.core.resource_conf.base_conf import password_decryptor
from cloudshell.shell.standards.core.resource_conf.resource_attr import AttrMeta
from cloudshell.shell.standards.core.resource_conf.attrs_getter import (
    MODEL,
    AbsAttrsGetter, RESOURCE_CONTEXT_TYPES,
)

from cloudshell.cp.gcp.helpers.converters import get_credentials

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
    credentials: Credentials = attr(
        ATTR_NAMES.json_keys,
        is_password=True,
        converter=get_credentials
    )
    custom_tags_list: list = attr(
        ATTR_NAMES.custom_tags,
        default=[],
    )
    availability_zone: str = attr(ATTR_NAMES.zone)

    def __attrs_post_init__(self):
        if isinstance(self.context, ResourceRemoteCommandContext):
            self.reservation_details = self.context.remote_reservation
        self.reservation_details = self.context.reservation

    @cached_property
    def reservation_info(self) -> ReservationInfo:
        if isinstance(self.context, ResourceRemoteCommandContext):
            return ReservationInfo.from_remote_resource_context(self.context)
        return ReservationInfo.from_resource_context(self.context)

    @cached_property
    def tags(self) -> dict:
        custom_tags = {tag.split("=")[0]: tag.split("=")[1] for tag in
                       self.custom_tags_list}
        default_tags = self._generate_default_tags()
        return {**default_tags, **custom_tags}

    def _generate_default_tags(self):
        return {
            "CreatedBy": "Quali",
            "Blueprint": self.reservation_details.environment_name,
            "Owner": self.reservation_details.owner_user,
            "Domain": self.reservation_details.domain,
            "ReservationId": self.reservation_details.reservation_id,
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
        attrs = ResourceInfoAttrGetter(cls, password_decryptor(api), details).get_attrs()
        converter = cls._CONVERTER(cls, attrs)
        return cls(
            name=details.Name,
            shell_name=details.ResourceModelName,
            family_name=details.ResourceFamilyName,
            address=details.Address,
            api=api,
            **converter.convert(),
        )
