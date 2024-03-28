"""
mqtt console with textual and aiomqtt
"""
import uuid, sys, os
import asyncio
from aiomqtt import Client, MqttError
from textual import work, on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, Container
from textual.widgets import Header, Footer, RichLog, Input, Select, Static,TabbedContent, TabPane, Label, Markdown
from textual.binding import Binding
from textual.suggester import SuggestFromList

try:
    from config import MQTT_HOST, MQTT_PORT, CLIENT_ID, MQTT_USER, MQTT_PASS
    CLIENT_ID = CLIENT_ID + str(uuid.uuid4)
except ModuleNotFoundError as _:
    MQTT_HOST = 'localhost'
    MQTT_PORT = 1883
    CLIENT_ID = 'textual-client-' + str(uuid.uuid4)
    # also set user and password if mqtt server needs it
    MQTT_USER = None
    MQTT_PASS = None

class MQTTConsole(App):
    """a simple mqtt console"""
    TITLE = "MQTT Console"
    BINDINGS = [Binding(key="q", action="quit_mqtt_console", description="Quit App"),
                Binding(key="c", action="clear_mqtt_console", description="Clear Console"),
                Binding("p", "show_tab('publishTab')", "Publish"),
                Binding("s", "show_tab('subscribeTab')", "Subscribe"),]
    CSS_PATH = "console-tui.tcss"
    #CSS_PATH = "testme.tcss"
    
    AUTO_FOCUS = "#publish"

    client = None

    #topiclist = ['textualize/rules', '#', 'homeassitant', 'tasmota', 'tele', 'textualize', 'home' ]
    topiclist = ['textualize/rules', 'homeassitant', 'tasmota', 'tele', 'textualize', 'home' ]
    current_topic = topiclist[0]

    def compose(self) -> ComposeResult:
        yield Header(name=self.TITLE, show_clock=False)
        yield Footer()
        with TabbedContent():
            with TabPane("Publish", id='publishTab'):
                yield Container(
                    Label('Topic'),
                    Label('Publish'),
                    id="label-horizontal",
                )
                yield Container(
                    Input(id='topic', placeholder=f"{self.current_topic}", suggester=SuggestFromList(self.topiclist, case_sensitive=True)),
                    Input(id='publish', placeholder=f"<- Publish a mqtt message"),
                    id="input-horizontal",
                )
                yield RichLog()
            with TabPane("Subscribe", id="subscribeTab"):
                yield Input(placeholder=f"subscribe to topic", id='subscribe')           
        

    def on_mount(self):
        self.mqttWorker()
        self.title = f'connected to {MQTT_HOST}'
        self.sub_title = f'Topic {self.current_topic}'
    
    @on(Input.Changed, '#topic')
    async def input_topic(self, message: Input.Changed) -> None:
        self.current_topic = message.value
        self.title = f'connected to {MQTT_HOST}'
        self.sub_title = f'Topic {self.current_topic}'
        self.query_one('#topic', Input).placeholder = self.current_topic

    @on(Input.Submitted, '#publish')
    async def input_publish(self, message: Input.Submitted) -> None:
        await self.client.publish(self.current_topic, f"{message.value}")
        self.query_one('#publish', Input).clear()

    @on(Input.Submitted, '#subscribe')
    async def input_subscribe(self, message: Input.Submitted) -> None:
        self.topiclist.append(message.value)
        await self.client.subscribe(f"{message.value}")
        self.query_one('#subscribe', Input).clear()
        
    @work(exclusive=False)
    async def mqttWorker(self):
        async with Client(MQTT_HOST, port=MQTT_PORT, identifier=CLIENT_ID, username=MQTT_USER, password=MQTT_PASS) as self.client:
            ## subscribe to the topic you also publishing
            await self.client.subscribe(self.current_topic)
            ## tasmota plugs
            #await self.client.subscribe("tele/#")
            #await self.client.subscribe("tasmota/discovery/#")
            ## subscribe to all
            #await self.client.subscribe("#")
            
            # doesnt work as expected (how to catch the input field ?)
            self.query_one('#publish', Input).has_focus = True

            ## or just use the self.topiclist
            ## hhhhm makes it slow (read more async stuff)
            #for topic in self.topiclist:
            #    await self.client.subscribe(topic)

            async for message in self.client.messages:
                t = message.topic.value
                ## somehow build the topiclist from reverse splitting with /
                ## now clue yet how that works
                #for item in t.split('/'):
                #    self.topiclist.append(item)
                #    self.query_one('#topic', Input).suggester = SuggestFromList(self.topiclist, case_sensitive=True)
                try:
                    msg = message.payload.decode('utf-8')
                except UnicodeDecodeError as _:
                    msg = "couldn't decode message"
                self.query_one(RichLog).write(f"{t}, {msg}")

    def action_show_tab(self, tab: str) -> None:
        """Switch to a new tab."""
        self.get_child_by_type(TabbedContent).active = tab

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