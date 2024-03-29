"""
mqtt console with textual and aiomqtt
"""
import uuid, sys, os
import asyncio
from aiomqtt import Client, MqttError
from textual import work, on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, Container
from textual.widgets import Switch, Header, Footer, RichLog, Input, Select, Static,TabbedContent, TabPane, Label, Markdown, SelectionList
from textual.binding import Binding
from textual.suggester import SuggestFromList
from textual.widgets.selection_list import Selection

try:
    from config import MQTT_HOST, MQTT_PORT, CLIENT_ID, MQTT_USER, MQTT_PASS, DEFAULT_SUB_LIST
    CLIENT_ID = CLIENT_ID + str(uuid.uuid4)
except ModuleNotFoundError as _:
    MQTT_HOST = 'localhost'
    MQTT_PORT = 1883
    CLIENT_ID = 'textual-client-' + str(uuid.uuid4)
    # also set user and password if mqtt server needs it
    MQTT_USER = None
    MQTT_PASS = None
    DEFAULT_SUB_LIST = ["tuning/#", "tele/+/LWT", "stat/+/RESULT", "tui/#"]

class MQTTConsole(App):
    """a simple mqtt console"""
    TITLE = "MQTT Console"
    BINDINGS = [Binding(key="q", action="quit_mqtt_console", description="Quit App"),
                Binding(key="c", action="clear_mqtt_console", description="Clear Console"),
                Binding(key="f", action="toggle_filter", description="Toggle Filter"),]
                #Binding("p", "show_tab('publishTab')", "Publish"),
    CSS_PATH = "console-tui.tcss"
    AUTO_FOCUS = "#publish"
    client = None
    filterlist = DEFAULT_SUB_LIST
    current_topic = 'textualize/rules'
    filter_on = False

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
                    Input(id='topic', placeholder=f"{self.current_topic}", suggester=SuggestFromList(self.filterlist, case_sensitive=True)),
                    Input(id='publish', placeholder=f"<- Publish a mqtt message"),
                    id="input-horizontal",
                )
                yield RichLog()
            with TabPane("Filter", id="filterTab"):
                yield Container(
                    Switch(value=self.filter_on,id='togglefilter'),
                    Input(placeholder=f"filter for topics", id='filter'),
                    id='filter-horizontal' ,
                )
                yield SelectionList[str](id='select')          
        

    def on_mount(self):
        self.mqttWorker()
        self.title = f'connected to {MQTT_HOST}'
        self.sub_title = f'Topic {self.current_topic}'
        self.sel = self.query_one('#select', SelectionList)
        for item in self.filterlist:
            self.sel.add_option(Selection(item, item, True))
    
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

    @on(Input.Submitted, '#filter')
    async def input_filter(self, message: Input.Submitted) -> None:
        if message.value == '#':
            sw = self.query_one('#togglefilter', Switch)
            sw.toggle()
            self.filter_on = sw.value
            self.query_one(RichLog).write(f"Filter: {sw.value} -- current filterlist is {self.filterlist}")
        else:
            self.filterlist.append(message.value)
            self.sel.add_option(Selection(message.value, message.value, True))
            self.query_one('#filter', Input).clear()
            self.query_one(RichLog).write(f"added filter: {message.value} -- current filterlist is {self.filterlist}")

    @on(Switch.Changed, '#togglefilter') 
    def toggle_filter_on_switch(self, message: Switch.Changed) -> None:
        self.filter_on = message.switch.value
        self.query_one(RichLog).write(f"Filter: {self.filter_on} -- current filterlist is {self.filterlist}")
        
    @on(SelectionList.SelectionToggled, '#select')
    async def delete_filter(self, message: SelectionList.SelectionToggled) -> None:
        self.filterlist.remove(message.selection.value)
        self.sel.clear_options()
        for item in self.filterlist:
            self.sel.add_option(Selection(item, item,True) )
        self.query_one(RichLog).write(f"deleted filter: {message.selection.value} -- current filterlist is {self.filterlist}")
      
    @work(exclusive=False)
    async def mqttWorker(self):
        async with Client(MQTT_HOST, port=MQTT_PORT, identifier=CLIENT_ID, username=MQTT_USER, password=MQTT_PASS) as self.client:
            ## subscribe to all 
            await self.client.subscribe("#")
            
            # doesnt work as expected (how to catch the input field ?)
            self.query_one('#publish', Input).has_focus = True
            
            # filter the messages with the filterlist
            async for message in self.client.messages:
                if self.filter_on == False:
                        t = message.topic.value
                        try:
                            msg = message.payload.decode('utf-8')
                        except UnicodeDecodeError as _:
                            msg = "couldn't decode message"
                        self.query_one(RichLog).write(f"{t}, {msg}")
                elif self.filter_on == True:
                    for filter in self.filterlist:
                        if message.topic.matches(filter):
                            t = message.topic.value
                            ## somehow build the filterlist from reverse splitting with /
                            ## now clue yet how that works
                            #for item in t.split('/'):
                            #    self.filterlist.append(item)
                            #    self.query_one('#topic', Input).suggester = SuggestFromList(self.filterlist, case_sensitive=True)
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
    
    def action_toggle_filter(self) -> None:
        self.query_one('#togglefilter',Switch).toggle()

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