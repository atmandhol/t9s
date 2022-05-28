import json
import yaml
from rich.console import RenderableType
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
from rich.traceback import Traceback
from textual.widget import Widget

from t9s.modules.kubernetes.objects import Resource
from t9s.modules.utils.enums import ObjectViewerFormat


# noinspection PyBroadException
class ObjectViewer(Widget):
    def __init__(self):
        super().__init__()
        self.resource: Resource = Resource(json_value={"message": "No Resource Selected"})
        self.format: ObjectViewerFormat = ObjectViewerFormat.YAML

    def render(self):
        syntax: RenderableType
        # TODO: Add toggles to give people choice to show these fields
        self.resource.json_value["metadata"].pop("managedFields") if (
            "metadata" in self.resource.json_value and "managedFields" in self.resource.json_value["metadata"]
        ) else None

        try:
            if self.format == ObjectViewerFormat.JSON:
                syntax = Syntax(json.dumps(self.resource.json_value, indent=2), "json", theme="native", line_numbers=True, word_wrap=True)
            elif self.format == ObjectViewerFormat.YAML:
                syntax = Syntax(
                    yaml.safe_dump(yaml.safe_load(json.dumps(self.resource.json_value))), "yaml", theme="native", line_numbers=True, word_wrap=True
                )
            else:
                syntax = Text("Logs")
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
        if self.format == ObjectViewerFormat.YAML:
            self.format = ObjectViewerFormat.JSON
        elif self.format == ObjectViewerFormat.JSON:
            self.format = ObjectViewerFormat.LOGS
        else:
            self.format = ObjectViewerFormat.YAML
        self.refresh(layout=True)
