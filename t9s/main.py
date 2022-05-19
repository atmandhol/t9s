from enum import Enum
from rich.console import Console
from modules.widgets.header import T9s_Header
from modules.widgets.footer import T9s_Footer
from modules.widgets.explorer import ExplorerTree
from textual.app import App
from textual.widgets import Placeholder

console = Console()


class Viewer(Enum):
    YAML = "yaml"
    LOGS = "logs"


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
        self.viewer = Viewer.YAML

    async def on_load(self) -> None:
        await self.bind("e", "view.toggle('explorer')", "Toggle Explorer")
        await self.bind("i", "view.toggle('info')", "Toggle Info")
        await self.bind("y", "logs_yaml_switcher()", "Toggle YAML/Logs")
        await self.bind("q", "quit", "Quit")

    async def on_mount(self) -> None:
        await self.view.dock(T9s_Header(), edge="top", size=8)
        await self.view.dock(T9s_Footer(), edge="bottom")
        await self.view.dock(ExplorerTree(console=console), edge="left", size=60, name="explorer")
        await self.view.dock(Placeholder(), edge="left", size=40, name="info")
        await self.view.dock(Placeholder(), edge="right", name="viewer")

    async def action_logs_yaml_switcher(self) -> None:
        if self.viewer == Viewer.YAML:
            self.viewer = Viewer.LOGS
        else:
            self.viewer = Viewer.YAML


T9s.run(console=console, log="textual.log")
