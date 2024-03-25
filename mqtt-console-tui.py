"""
mqtt console with textual and aiomqtt
"""
import uuid, sys, os
from aiomqtt import Client
from textual import work, on
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, RichLog, Input, Select, Static
from textual.binding import Binding
from textual.suggester import SuggestFromList



try:
    from config import MQTT_HOST, MQTT_PORT, CLIENT_ID, MQTT_USER, MQTT_PW
    CLIENT_ID = CLIENT_ID + str(uuid.uuid4)
except ModuleNotFoundError as _:
    MQTT_HOST = 'fill in your mqtt host here'
    MQTT_PORT = 'add your mqtt port here'
    CLIENT_ID = 'put your client id here' + str(uuid.uuid4)
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

    topiclist = ['textualize/rules', '#', 'homeassitant', 'tasmota', 'tele', 'textualize', 'home' ]
    topic = topiclist[0]

    def compose(self) -> ComposeResult:
        yield Header(name=self.TITLE, show_clock=False)
        yield Static('Topic')
        yield Static('Publish')
        yield Input(placeholder=f"{self.topic}", id='topic', suggester=SuggestFromList(self.topiclist, case_sensitive=True))
        yield Input(placeholder=f"<- Publish a mqtt message on", id='publish')
        yield RichLog()
        yield Footer()

    def on_mount(self):
        self.mqttWorker()    
    
    @on(Input.Submitted)
    async def input_submitted(self, message: Input.Submitted) -> None:
        if message.input.id == 'topic':
            self.topic = message.value
            self.query_one('#topic', Input).placeholder = self.topic
        elif message.input.id == 'publish':
            await self.client.publish(self.topic, f"{message.value}")
            self.query_one('#publish', Input).clear()
        
    @work(exclusive=False)
    async def mqttWorker(self):
        async with Client(MQTT_HOST, port=MQTT_PORT, identifier=CLIENT_ID, username=MQTT_USER, password=MQTT_PW) as self.client:
            ## subscribe to the topic you also publishing
            await self.client.subscribe(self.topic)
            ## tasmota plugs
            await self.client.subscribe("tele/#")
            #await self.client.subscribe("tasmota/discovery/#")
            ## subscribe to all
            await self.client.subscribe("#")

            async for message in self.client.messages:
                t = message.topic.value
                ## somehow build the topiclist from reverse splitting with /
                ## now clue yet how that works
                #item = t.rsplit('/')
                #while item:
                #    self.topiclist.append(item)
                #self.query_one('#topic', Input).suggester = SuggestFromList(self.topiclist, case_sensitive=True)
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