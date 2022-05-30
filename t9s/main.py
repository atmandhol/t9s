"""
TODO: Add a style config file and use that all over the project so people can theme it later
"""
import sys

from rich.console import Console

from t9s.modules.widgets.log_viewer import LogViewer, LogUpdate
from t9s.modules.widgets.header import T9s_Header
from t9s.modules.widgets.footer import T9s_Footer
from t9s.modules.widgets.explorer import ExplorerTree
from t9s.modules.widgets.viewer import ObjectViewer
from t9s.modules.widgets.info import ObjectInfo
from t9s.modules.kubernetes.objects import Resource
from textual.app import App
from textual.widgets import ScrollView, TreeControl

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
        await self.bind("e", "view.toggle('explorer')", "Toggle Explorer")
        await self.bind("i", "view.toggle('info')", "Toggle Info")
        await self.bind("y", "yaml_json_switcher()", "Toggle YAML/JSON")
        await self.bind("l", "logs_switcher()", "Toggle Logs")
        await self.bind("k", "live_logs_switcher()", "Toggle Live Logs")
        await self.bind("1", "focus_explorer()", "Focus Explorer", show=False)
        await self.bind("2", "focus_info()", "Focus Info", show=False)
        await self.bind("3", "focus_viewer()", "Focus Viewer", show=False)
        await self.bind("q", "quit", "Quit")

    # noinspection PyAttributeOutsideInit
    async def on_mount(self) -> None:
        self.explorer = ExplorerTree(console=console)
        self.explorer_panel = ScrollView(contents=self.explorer, auto_width=True)
        self.info = ObjectInfo()
        self.info_panel = ScrollView(contents=self.info)
        self.viewer = ObjectViewer()
        self.viewer_panel = ScrollView(contents=self.viewer)
        self.log_viewer = LogViewer()
        self.log_viewer_panel = ScrollView(contents=self.log_viewer)
        self.log_viewer_panel.visible = False

        await self.view.dock(T9s_Header(), edge="top", size=8)
        await self.view.dock(T9s_Footer(), edge="bottom")
        await self.view.dock(self.explorer_panel, edge="left", size=60, name="explorer")
        await self.view.dock(self.info_panel, edge="left", size=60, name="info")
        await self.view.dock(self.viewer_panel, edge="left", name="viewer")
        await self.view.dock(self.log_viewer_panel, edge="left", name="log_viewer")

    async def action_yaml_json_switcher(self) -> None:
        self.viewer.switch_format()
        await self.viewer_panel.update(self.viewer.render())

    async def action_live_logs_switcher(self) -> None:
        if self.log_viewer.live_reload:
            self.log_viewer.set_live_reload(False)
        else:
            self.log_viewer.set_live_reload(True)
        await self.log_viewer_panel.update(self.log_viewer.render())

    async def action_focus_explorer(self) -> None:
        await self.explorer.focus()

    async def action_focus_info(self) -> None:
        await self.info.focus()

    async def action_focus_viewer(self) -> None:
        await self.viewer.focus()

    async def action_logs_switcher(self) -> None:
        if self.viewer_panel.visible:
            self.viewer_panel.visible = False
            self.log_viewer_panel.visible = True
        else:
            self.viewer_panel.visible = True
            self.log_viewer_panel.visible = False

    async def handle_tree_click(self, message: TreeControl[Resource]) -> None:
        if message.node.data.kind not in ["Context", "Namespace"]:
            self.info.update_resource(resource=message.node.data)
            await self.info_panel.update(self.info.render())
            self.viewer.update_resource(resource=message.node.data)
            await self.viewer_panel.update(self.viewer.render())
            self.log_viewer.update_resource(resource=message.node.data)
            await self.log_viewer_panel.update(self.log_viewer.render())

    async def handle_log_update(self, message: LogUpdate) -> None:
        if self.log_viewer.live_reload:
            await self.log_viewer_panel.update(message.render_op, home=False)
            self.log_viewer_panel.scroll_in_to_view(9999999999)

    async def shutdown(self):
        self.log_viewer.reset()
        await super().shutdown()
        sys.exit(0)


T9s.run(console=console, log="textual.log")
