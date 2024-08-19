import re

GCP_NAME_PATTERN = r"(?:[a-z](?:[-a-z0-9]{0,61}[a-z0-9])?)"
pattern_remove_symbols = re.compile(rf"[^\w\d\-\.]")


def generate_name(name: str) -> str:
    new_name = name.lower().replace("-", "--")
    new_name = pattern_remove_symbols.sub("", new_name)
    return re.sub(r"[^a-z0-9-]", "-", new_name)


def generate_vpc_name(name: str) -> str:
    return f"quali-{generate_name(name)}"
