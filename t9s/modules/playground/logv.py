
from threading import Thread
from typing import Type

import rich.repr
from kubernetes.watch import watch
from textual import events
# noinspection PyProtectedMember
from textual._types import MessageTarget
from textual.app import App
from textual.driver import Driver
from textual.message import Message
from textual.widgets import Header, Footer, ScrollView
from rich.console import RenderableType
from rich.text import Text
from textual.widget import Widget
from kubernetes import client, config
from rich.panel import Panel
from t9s.modules.kubernetes.commons import Commons
from rich.console import Console
from queue import Queue

console = Console()
config.load_kube_config()
v1 = client.CoreV1Api()
commons = Commons(logger=None)
pod_name = "ss-00006-deployment-7d8659988c-g7x4v"
namespace = "ns1"


@rich.repr.auto
class LogUpdate(Message, bubble=True):
    def __init__(self, sender: MessageTarget, render_op) -> None:
        self.render_op = render_op
        super().__init__(sender)


# noinspection PyBroadException
class LogViewer(Widget):
    def __init__(self):
        super().__init__()
        self.logs: str = ""
        self.futures = list()
        self.q: Queue = Queue()
        self.t = Thread(target=self.watch_pod_logs, args=[self.q])
        self.t.start()

    @staticmethod
    def watch_pod_logs(q):
        w = watch.Watch()
        for event in w.stream(
                v1.read_namespaced_pod_log,
                name=pod_name,
                namespace=namespace,
                container="workload",
                pretty="true",
                since_seconds=86400,
                tail_lines=500,
                timestamps=False,
        ):
            q.put_nowait(event)

    def render(self):
        syntax: RenderableType
        while not self.q.empty():
            self.logs = self.logs + "\n" + self.q.get(block=False)
        syntax = Text(self.logs)
        return Panel(
            syntax,
            title=f"[bold][#ebae3d]Logs[/#ebae3d]",
            border_style="#69b4ff",
        )

    async def on_mount(self, event: events.Mount) -> None:
        # TODO make interval configurable
        self.set_interval(0.5, callback=self.refresh)
        pass

    async def on_timer(self, event: events.Timer) -> None:
        await self.emit(LogUpdate(self, render_op=self.render()))


class MyApp(App):
    """An example of a very simple Textual App"""

    def __init__(
        self,
        screen: bool = True,
        driver_class: Type[Driver] | None = None,
        log: str = "",
        log_verbosity: int = 1,
        title: str = "Textual Application",
    ):
        super().__init__(screen, driver_class, log, log_verbosity, title)
        self.log_view = None
        self.log_viewer = None
        self.header = None

    async def on_load(self) -> None:
        """Sent before going in to application mode."""
        # Bind our basic keys
        await self.bind("q", "quit", "Quit")

    async def on_mount(self) -> None:
        """Call after terminal goes in to application mode"""
        self.log_viewer = LogViewer()
        self.log_view = ScrollView(self.log_viewer)
        self.header = Header()
        # Dock our widgets
        await self.view.dock(self.header, edge="top")
        await self.view.dock(Footer(), edge="bottom")

        # Note the directory is also in a scroll view
        await self.view.dock(self.log_view, edge="top", name="log_viewer")

    async def handle_log_update(self, message: LogUpdate) -> None:
        await self.log_view.update(message.render_op, home=False)
        self.log_view.scroll_in_to_view(9999999999)


# Run our app class
MyApp.run(title="Log Viewer", log="textual.log")
