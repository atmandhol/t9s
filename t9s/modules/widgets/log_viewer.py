import threading

import rich.repr
from queue import Queue

from kubernetes.watch import watch
from rich.console import RenderableType
from rich.panel import Panel
from rich.text import Text
from textual import events

# noinspection PyProtectedMember
from textual._types import MessageTarget
from textual.message import Message
from textual.widget import Widget

from t9s.modules.kubernetes.commons import Commons
from t9s.modules.kubernetes.k8s import K8s
from t9s.modules.kubernetes.objects import Resource


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
            since_seconds=7*86400,
            tail_lines=100,
            timestamps=False,
        ):
            if self.stopped():
                return
            self.q.put_nowait(f"[{self.container}]: {event}")


class LogViewer(Widget):
    def __init__(self):
        super().__init__()
        self.k8s_helper = K8s(logger=self.log)
        self.commons = Commons(logger=self.log)
        self.logs: str = ""
        self.live_reload = True
        self.resource: Resource = Resource(json_value={"message": "No Resource Selected"})
        self.q: Queue = Queue()
        self.log_threads: list[LogThread] = list()

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

    async def on_timer(self, event: events.Timer) -> None:
        if self.live_reload:
            await self.emit(LogUpdate(self, render_op=self.render()))

    def set_live_reload(self, value: bool):
        self.live_reload = value

    def update_resource(self, resource: Resource) -> None:
        # Stop all running threads
        for t in self.log_threads:
            t.stop()
        # Cleanup old state
        self.log_threads = list()
        self.q = Queue()
        self.logs = ""
        self.resource = resource

        if self.resource.kind == "Pod":
            # Get containers
            containers = list()
            for container in self.resource.json_value["spec"]["containers"]:
                containers.append(container["name"])
            for container in containers:
                t = LogThread(self.q, self.k8s_helper.core_clients[self.resource.context], self.resource.name, self.resource.namespace, container)
                self.log_threads.append(t)
                t.start()
        else:
            self.logs = "No Logs to show"

        self.refresh(layout=True)
