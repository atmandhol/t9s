from dataclasses import dataclass


@dataclass
class Resource:
    name: str = None
    kind: str = None
    context: str = None
    namespace: str = None
    uid: str = None
    owner: str = None
    has_children: bool = False
    metadata: dict = None
    spec: dict = None
    status: dict = None
    json_value: dict = None
    yaml_value: str = None


@dataclass
class CustomResourceDefinition:
    group: str
    kind: str
    plural: str
    scope: str = None
    version: str = None
    printer_cols: list = None
