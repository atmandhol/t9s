import threading
import random
import time

import rich.repr

from queue import Queue
from kubernetes.watch import watch
from rich.console import RenderableType
from rich.panel import Panel
from textual import events

# noinspection PyProtectedMember
from textual._types import MessageTarget
from textual.message import Message
from textual.widget import Widget

from t9s.modules.kubernetes.commons import Commons
from t9s.modules.kubernetes.k8s import K8s
from t9s.modules.kubernetes.objects import Resource, LogEvent

rich_logger_colors = [
    "#faa005",
    "#d49f7f",
    "#edda7b",
    "#bbd620",
    "#20d629",
    "#20d6a3",
    "#2fd6d1",
    "#4dc0e3",
    "#4d9be3",
    "#949feb",
    "#bf94eb",
    "#e094eb",
    "#d945bb",
    "#c78595",
]


@rich.repr.auto
class LogUpdate(Message, bubble=True):
    def __init__(self, sender: MessageTarget, render_op) -> None:
        self.render_op = render_op
        super().__init__(sender)


class LogThread(threading.Thread):
    def __init__(self, q, client, pod, namespace, container, *args, **kwargs):
        super(LogThread, self).__init__(*args, **kwargs)
        self._stop = threading.Event()
        self.q = q
        self.client = client
        self.pod = pod
        self.namespace = namespace
        self.container = container
        self.color = random.choice(rich_logger_colors)

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.is_set()

    def run(self):
        w = watch.Watch()
        for event in w.stream(
            self.client.read_namespaced_pod_log,
            name=self.pod,
            namespace=self.namespace,
            container=self.container,
            pretty="true",
            since_seconds=7 * 86400,
            tail_lines=100,
            timestamps=True,
        ):
            if self.stopped():
                w.stop()
                return
            self.q.put_nowait(
                LogEvent(
                    group=f"[bold][{self.color}]<{self.container}>[/{self.color}][/bold]", msg="".join(event.split(" ")[1:]), ts=event.split(" ")[0]
                )
            )


class LogViewer(Widget):
    def __init__(self):
        super().__init__()
        self.k8s_helper = K8s(logger=self.log)
        self.commons = Commons(logger=self.log)
        self.logs: list[LogEvent] = list()
        self.live_reload = True
        self.resource: Resource = Resource(json_value={"message": "No Resource Selected"})
        self.q: Queue[LogEvent] = Queue()
        self.log_threads: list[LogThread] = list()

    def generate_log_str(self) -> str:
        op = str()
        for log in self.logs:
            op = op + f"{log.group}: {log.msg}\n"
        return op

    def render(self):
        syntax: RenderableType
        while not self.q.empty():
            self.logs.append(self.q.get(block=False))
        if len(self.logs) > 0:

            self.logs.sort(key=lambda x: x.ts)
        syntax = self.generate_log_str()
        return Panel(
            syntax,
            title=f"[bold][#ebae3d]Logs[/#ebae3d]: {self.resource.name} - Live Reload: [{self.live_reload}]",
            border_style="#69b4ff",
        )

    async def on_mount(self, event: events.Mount) -> None:
        # TODO make interval configurable
        self.set_interval(0.5, callback=self.refresh)

    async def on_timer(self, event: events.Timer) -> None:
        if self.live_reload:
            await self.emit(LogUpdate(self, render_op=self.render()))

    def set_live_reload(self, value: bool):
        self.live_reload = value

    def update_resource(self, resource: Resource) -> None:
        self.reset()
        self.resource = resource
        if self.resource.kind == "Pod":
            # Get containers
            containers = list()
            for container in self.resource.json_value["spec"]["containers"]:
                containers.append(container["name"])
            for container in self.resource.json_value["spec"]["initContainers"]:
                containers.append(container["name"])
            for container in containers:
                t = LogThread(self.q, self.k8s_helper.core_clients[self.resource.context], self.resource.name, self.resource.namespace, container)
                self.log_threads.append(t)
                t.start()
        else:
            self.logs = [LogEvent(group=f"[bold]t9s[/bold]", ts=str(int(time.time())), msg="No Logs to show")]
        self.refresh(layout=True)

    def reset(self):
        # Stop all running threads
        for t in self.log_threads:
            t.stop()
        # Cleanup old state
        self.log_threads = list()
        self.q = Queue()
        self.logs = list()
