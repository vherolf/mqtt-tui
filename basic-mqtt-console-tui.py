"""
A basic mqtt console example with textual and aiomqtt
"""
from aiomqtt import Client
from textual import work, on
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, RichLog, Input
from textual.binding import Binding

try:
    from config import MQTT_HOST, MQTT_PORT, CLIENT_ID, MQTT_USER, MQTT_PW
except ModuleNotFoundError as _:
    MQTT_HOST = 'fill in your mqtt host here'
    MQTT_PORT = 'add your mqtt port here'
    CLIENT_ID = 'put your client id here'
    # also set user and password if mqtt server needs it
    MQTT_USER = None
    MQTT_PW   = None

class MQTTConsole(App):
    """a basic mqtt console example"""
    TITLE = "MQTT Console"
    BINDINGS = [Binding(key="q", action="quit_mqtt_console", description="Quit App"),
                Binding(key="c", action="clear_mqtt_console", description="Clear Console"),]

    client = None
    # the topic you wanna publish to
    topic = f"textualize/rules"

    def compose(self) -> ComposeResult:
        yield Header(name=self.TITLE, show_clock=False)
        yield Input(placeholder=f"Publish a mqtt message on topic {self.topic}")
        yield RichLog()
        yield Footer()

    def on_mount(self):
        self.mqttWorker()

    @on(Input.Submitted)
    async def input_submitted(self, message: Input.Submitted) -> None:
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
    app = MQTTConsole()
    app.run()