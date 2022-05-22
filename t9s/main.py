from rich.console import Console

from modules.widgets.header import T9s_Header
from modules.widgets.footer import T9s_Footer
from modules.widgets.explorer import ExplorerTree
from modules.widgets.object_viewer import ObjectViewer
from modules.kubernetes.objects import Resource
from textual.app import App
from textual.widgets import Placeholder, ScrollView, TreeControl

console = Console()


# noinspection PyBroadException
class T9s(App):
    def __init__(
        self,
        screen: bool = True,
        driver_class=None,
        log: str = "",
        log_verbosity: int = 1,
        title: str = "t9s",
    ):
        super().__init__(screen, driver_class, log, log_verbosity, title)
        self.explorer = None

    async def on_load(self) -> None:
        await self.bind("e", "view.toggle('explorer')", "Toggle Explorer Panel")
        await self.bind("x", "focus_explorer()", "Focus Explorer")
        await self.bind("i", "view.toggle('info')", "Toggle Info")
        await self.bind("c", "focus_info()", "Focus Info")
        await self.bind("y", "yaml_json_switcher()", "Toggle YAML/JSON")
        await self.bind("q", "quit", "Quit")

    # noinspection PyAttributeOutsideInit
    async def on_mount(self) -> None:
        self.explorer = ExplorerTree(console=console)
        self.explorer_panel = ScrollView(contents=self.explorer)
        self.viewer = ObjectViewer()
        self.viewer_panel = ScrollView(contents=self.viewer)
        await self.view.dock(T9s_Header(), edge="top", size=8)
        await self.view.dock(T9s_Footer(), edge="bottom")
        await self.view.dock(self.explorer_panel, edge="left", size=60, name="explorer")
        await self.view.dock(Placeholder(), edge="left", size=40, name="info")
        await self.view.dock(self.viewer_panel, edge="right", name="viewer")

    async def action_yaml_json_switcher(self) -> None:
        self.viewer.switch_format()
        await self.viewer_panel.update(self.viewer.render())

    async def action_focus_explorer(self) -> None:
        await self.explorer.focus()

    async def action_focus_info(self) -> None:
        pass

    async def handle_tree_click(self, message: TreeControl[Resource]) -> None:
        if message.node.data.kind not in ["Context", "Namespace"]:
            self.viewer.update_resource(resource=message.node.data)
            await self.viewer_panel.update(self.viewer.render())


T9s.run(console=console, log="textual.log")
