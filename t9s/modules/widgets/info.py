from rich.console import RenderableType
from rich.panel import Panel
from rich import box
from rich.console import Group
from rich.table import Table
from rich.text import Text
from rich.traceback import Traceback
from textual.widget import Widget

from modules.kubernetes.objects import Resource
from modules.utils.enums import ObjectViewerFormat


# noinspection PyBroadException
class ObjectInfo(Widget):
    def __init__(self):
        super().__init__()
        self.resource: Resource = Resource(yaml_value="No Resource Selected", json_value={"message": "No Resource Selected"})
        self.format: ObjectViewerFormat = ObjectViewerFormat.YAML

    def render(self):
        panel_group: RenderableType
        try:
            panel_group = Group(
                self.render_summary_table(),
                self.render_label_table(),
                self.render_anno_table(),
                Panel(Text(), title="Live Tree"),
            )
        except Exception:
            panel_group = Traceback(theme="monokai", width=None, show_locals=True)
        return Panel(
            panel_group,
            title=f"",
            border_style="#69b4ff",
        )

    def render_summary_table(self):
        summary_table = Table(title="Summary", title_justify="left", box=box.HORIZONTALS, show_header=False, expand=True)
        summary_table.add_column("", style="bold #69b4ff")
        summary_table.add_column("", style="bold white")
        summary_table.add_row("kind", f"{self.resource.kind}")
        summary_table.add_row("name", f"{self.resource.name}")
        summary_table.add_row("namespace", f"{self.resource.namespace}")
        return summary_table

    def render_anno_table(self):
        anno_table = Table(title="Annotation", title_justify="left", box=box.HORIZONTALS, show_header=False, expand=True)
        anno_table.add_column("", style="bold #69b4ff", no_wrap=True)
        annotations = self.resource.json_value.get("metadata", {}).get("annotations", {})
        for anno in annotations:
            anno_table.add_row(anno)
            anno_table.add_row(f"[bold][white]{annotations[anno]}[/white][/bold]")
        return anno_table

    def render_label_table(self):
        label_table = Table(title="Labels", title_justify="left", box=box.HORIZONTALS, show_header=False, expand=True)
        label_table.add_column("", style="bold #69b4ff", no_wrap=True)
        label_table.add_column("", style="bold white", no_wrap=True)
        labels = self.resource.json_value.get("metadata", {}).get("labels", {})
        for label in labels:
            label_table.add_row(label, labels[label])
        return label_table

    def update_resource(self, resource: Resource) -> None:
        self.resource = resource
        self.refresh(layout=True)
