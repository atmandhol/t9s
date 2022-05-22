import json
import yaml
from rich.console import RenderableType
from rich.panel import Panel
from rich.syntax import Syntax
from rich.traceback import Traceback
from textual.widget import Widget

from modules.kubernetes.objects import Resource
from modules.utils.enums import ObjectViewerFormat


# noinspection PyBroadException
class ObjectViewer(Widget):
    def __init__(self):
        super().__init__()
        self.resource: Resource = Resource(yaml_value="No Resource Selected", json_value={"message": "No Resource Selected"})
        self.format: ObjectViewerFormat = ObjectViewerFormat.YAML

    def render(self):
        syntax: RenderableType
        try:
            if self.format == ObjectViewerFormat.JSON:
                syntax = Syntax(json.dumps(self.resource.json_value, indent=2), "json", theme="native", line_numbers=True, word_wrap=True)
            else:
                syntax = Syntax(yaml.safe_dump(self.resource.yaml_value), "yaml", theme="native", line_numbers=True, word_wrap=True)
        except Exception:
            syntax = Traceback(theme="monokai", width=None, show_locals=True)
        return Panel(
            syntax,
            title=f"[bold][#ebae3d]{self.resource.context}[/#ebae3d]/[#39cbf7]{self.resource.namespace}[/#39cbf7]/[white]{self.resource.kind}[/white]/[#b8b6b6]{self.resource.name}[/#b8b6b6][/bold]",
            border_style="#69b4ff",
        )

    def update_resource(self, resource: Resource) -> None:
        self.resource = resource
        self.refresh(layout=True)

    def switch_format(self) -> None:
        if self.format == ObjectViewerFormat.JSON:
            self.format = ObjectViewerFormat.YAML
        else:
            self.format = ObjectViewerFormat.JSON
        self.refresh(layout=True)
