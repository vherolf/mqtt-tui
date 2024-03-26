"""
mqtt buttons made with textual and aiomqtt
"""
import uuid, sys, os
import asyncio
from aiomqtt import Client, MqttError
from textual import work, on
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, RichLog, Input, Select, Static, Button
from textual.binding import Binding
from textual.suggester import SuggestFromList

try:
    from config import MQTT_HOST, MQTT_PORT, CLIENT_ID, MQTT_USER, MQTT_PW
    CLIENT_ID = CLIENT_ID + str(uuid.uuid4)
except ModuleNotFoundError as _:
    MQTT_HOST = 'localhost'
    MQTT_PORT = 1883
    CLIENT_ID = 'buttonizer' + str(uuid.uuid4)
    # also set user and password if mqtt server needs it
    MQTT_USER = None
    MQTT_PW   = None

class Buttonizer(App):
    TITLE = "Buttonizer"
    BINDINGS = [Binding(key="q", action="quit_buttonizer", description="Quit App"),]
    
    client = None

    def compose(self) -> ComposeResult:
        yield Header(name=self.TITLE, show_clock=False)
        yield Button()
        yield Button()
        yield Footer()

    def on_mount(self):
        self.mqttWorker()    
    
    @work(exclusive=False)
    async def mqttWorker(self):
        async with Client(MQTT_HOST, port=MQTT_PORT, identifier=CLIENT_ID, username=MQTT_USER, password=MQTT_PW) as self.client:
            ## tasmota plugs
            await self.client.subscribe("tele/#")
            await self.client.subscribe("tasmota/discovery/#")
            
            async for message in self.client.messages:
                t = message.topic.value
                try:
                    msg = message.payload.decode('utf-8')
                except UnicodeDecodeError as _:
                    msg = "couldn't decode message"
                self.query_one(RichLog).write(f"{t}, {msg}")


    def action_quit_buttonizer(self) -> None:
        self.app.exit()

if __name__ == "__main__":
    # https://github.com/sbtinstruments/aiomqtt#note-for-windows-users
    # Change to the "Selector" event loop if platform is Windows
    if sys.platform.lower() == "win32" or os.name.lower() == "nt":
        from asyncio import set_event_loop_policy, WindowsSelectorEventLoopPolicy
        set_event_loop_policy(WindowsSelectorEventLoopPolicy())
    app = Buttonizer()
    app.run()