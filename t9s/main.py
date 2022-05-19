from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.containers import VSplit, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.key_binding import KeyBindings

kb = KeyBindings()
buffer1 = Buffer()

root_container = VSplit([
    Window(content=BufferControl(buffer=buffer1)),
    Window(width=1, char='|'),
    Window(content=FormattedTextControl(text='Hello world')),
])

layout = Layout(root_container)


@kb.add('c-q')
def exit_(event):
    """
    Pressing Ctrl-Q will exit the user interface.

    Setting a return value means: quit the event loop that drives the user
    interface and return this value from the `Application.run()` call.
    """
    event.app.exit()


app = Application(layout=layout, full_screen=True, key_bindings=kb)
app.run()
