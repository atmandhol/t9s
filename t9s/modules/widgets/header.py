from rich.panel import Panel
from textual.reactive import Reactive
from textual.widget import Widget
import pyfiglet


class T9s_Header(Widget):
    def __init__(self):
        super().__init__()
        self.mouse_over = Reactive(False)

    def render(self) -> Panel:
        return Panel(pyfiglet.Figlet(font="speed", width=40).renderText("t9s"), style="bold #69b4ff", border_style="black")

    def on_enter(self) -> None:
        self.mouse_over = True

    def on_leave(self) -> None:
        self.mouse_over = False
