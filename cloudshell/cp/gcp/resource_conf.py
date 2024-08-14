from __future__ import annotations

from collections.abc import Callable

from attr import define, Attribute
from cloudshell.api.cloudshell_api import ResourceInfo, CloudShellAPISession
from cloudshell.shell.standards.core.namespace_type import NameSpaceType
from cloudshell.shell.standards.core.resource_conf import attr, BaseConfig
from cloudshell.shell.standards.core.resource_conf.base_conf import password_decryptor
from cloudshell.shell.standards.core.resource_conf.resource_attr import AttrMeta
from cloudshell.shell.standards.core.resource_conf.attrs_getter import (
    MODEL,
    AbsAttrsGetter,
)


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
    machine_type = "Machine Type"
    custom_tags = "Custom Tags"
    networks_in_use = "Networks in use"


@define(slots=False, str=False)
class GCPResourceConfig(BaseConfig):
    ATTR_NAMES = GCPAttributeNames

    region: str = attr(ATTR_NAMES.region)
    machine_type: str = attr(ATTR_NAMES.machine_type)
    networks_in_use: str = attr(ATTR_NAMES.networks_in_use)
    json_keys: str = attr(ATTR_NAMES.json_keys, is_password=True)
    _custom_tags: list[str] = attr(ATTR_NAMES.custom_tags, default={})
    availability_zone: str = attr(ATTR_NAMES.zone)

    @property
    def custom_tags(self) -> dict:
        return {tag.split("=")[0]: tag.split("=")[1] for tag in self._custom_tags}

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
