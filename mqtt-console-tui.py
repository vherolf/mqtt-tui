"""
simple mqtt console with textual and aiomqtt
"""
import uuid, sys, os
from aiomqtt import Client
from textual import work, on
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Header, Footer, RichLog, Input
from textual.binding import Binding

try:
    from config import MQTT_HOST, MQTT_PORT, CLIENT_ID, MQTT_USER, MQTT_PW
    CLIENT_ID = CLIENT_ID + str(uuid.uuid1().bytes)
except ModuleNotFoundError as _:
    MQTT_HOST = 'fill in your mqtt host here'
    MQTT_PORT = 'add your mqtt port here'
    CLIENT_ID = 'put your client id here' + str(uuid.uuid1().bytes)
    # also set user and password if mqtt server needs it
    MQTT_USER = None
    MQTT_PW   = None

class MQTTConsole(App):
    """a simple mqtt console"""
    TITLE = "MQTT Console"
    BINDINGS = [Binding(key="q", action="quit_mqtt_console", description="Quit App"),
                Binding(key="c", action="clear_mqtt_console", description="Clear Console"),]
    CSS_PATH = "console-tui.tcss"

    client = None
    # the topic you wanna publish to
    topic = f"textualize/rules"

    def compose(self) -> ComposeResult:
        yield Header(name=self.TITLE, show_clock=False)
        yield Input(placeholder=f"Publish a mqtt message on topic {self.topic}", id='publish')
        yield Input(placeholder=f"{self.topic}", id='topic')
        yield RichLog()
        yield Footer()

    def on_mount(self):
        self.mqttWorker()    # https://github.com/sbtinstruments/aiomqtt#note-for-windows-users
    # Change to the "Selector" event loop if platform is Windows
    if sys.platform.lower() == "win32" or os.name.lower() == "nt":
        from asyncio import set_event_loop_policy, WindowsSelectorEventLoopPolicy
        set_event_loop_policy(WindowsSelectorEventLoopPolicy())

    @on(Input.Submitted)
    async def input_submitted(self, message: Input.Submitted) -> None:
        if message.input.id == 'topic':
            self.topic = message.value
            #self.query_one("#topic")
        elif message.input.id == 'publish':
            await self.client.publish(self.topic, f"{message.value}")
        
    @work(exclusive=False)
    async def mqttWorker(self):
        async with Client(MQTT_HOST, port=MQTT_PORT, identifier=CLIENT_ID, username=MQTT_USER, password=MQTT_PW) as self.client:
            ## subscribe to the topic you also publishing
            await self.client.subscribe(self.topic)
            ## tasmota plugs
            await self.client.subscribe("tele/#")
            #await self.client.subscribe("tasmota/discovery/#")
            ## subscribe to all
            #await self.client.subscribe("#")

            async for message in self.client.messages:
                t = message.topic.value
                try:
                    msg = message.payload.decode('utf-8')
                except UnicodeDecodeError as _:
                    msg = "couldn't decode message"
                self.query_one(RichLog).write(f"{t}, {msg}")
    
    def action_clear_mqtt_console(self) -> None:
        self.query_one(RichLog).clear()

    def action_quit_mqtt_console(self) -> None:
        self.app.exit()

if __name__ == "__main__":
    # https://github.com/sbtinstruments/aiomqtt#note-for-windows-users
    # Change to the "Selector" event loop if platform is Windows
    if sys.platform.lower() == "win32" or os.name.lower() == "nt":
        from asyncio import set_event_loop_policy, WindowsSelectorEventLoopPolicy
        set_event_loop_policy(WindowsSelectorEventLoopPolicy())
    app = MQTTConsole()
    app.run()