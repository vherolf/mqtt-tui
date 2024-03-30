"""
mqtt buttons made with textual and aiomqtt
"""
import uuid, sys, os
import json
import asyncio
from aiomqtt import Client, MqttError
from textual import work, on
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, RichLog, Input, Select, Static, Button, RichLog
from textual.binding import Binding
from textual.suggester import SuggestFromList
from textual.containers import Horizontal, Vertical, Container
from textual import log

try:
    from config import MQTT_HOST, MQTT_PORT, CLIENT_ID, MQTT_USER, MQTT_PASS
    CLIENT_ID = CLIENT_ID + str(uuid.uuid4)
except ModuleNotFoundError as _:
    MQTT_HOST = 'localhost'
    MQTT_PORT = 1883
    CLIENT_ID = 'buttonizer' + str(uuid.uuid4)
    # also set user and password if mqtt server needs it
    MQTT_USER = None
    MQTT_PASS   = None

class Buttonizer(App):
    TITLE = "Buttonizer"
    BINDINGS = [Binding(key="q", action="quit_buttonizer", description="Quit App"),]
    buttonlist = []
    client = None

    def compose(self) -> ComposeResult:
        yield Header(name=self.TITLE, show_clock=False)
        yield Container(
            #Button(id='lupenlampe'),
            id="buttons",
        )
        yield RichLog()
        yield Footer()

    def on_mount(self):
        self.mqttWorker()
        #self.add_button('lupenlampe')
        
    def add_button(self, name):
        self.buttonlist.append(name)
        self.query_one('#buttons', Container).mount(Button(id=name))
    
    def is_json(myjson):
        """check if a string is json"""
        try:
            j = json.loads(myjson)
        except ValueError as _:
            return ""
        return j

    @on(Button.Pressed)
    async def toggle_plug(self, message: Button.Pressed) -> None:
        id = message.button.id
        name = message.button.name
        self.query_one(RichLog).write(f"pressed me {message.button}, {name}, {id}")
        topic = f'cmnd/{id}/POWER'
        payload = 'TOGGLE'
        await self.publish_mqtt(topic, payload)

    async def publish_mqtt(self,topic, payload):
        await self.client.publish(f'{topic}', f'{payload}')

    @work(exclusive=False)
    async def mqttWorker(self):
        async with Client(MQTT_HOST, port=MQTT_PORT, identifier=CLIENT_ID, username=MQTT_USER, password=MQTT_PASS) as self.client:
            ## tasmota plugs
            await self.client.subscribe("#")
            #await self.client.subscribe("tasmota/discovery/#")
            
            async for message in self.client.messages:
                t = message.topic.value
                try:
                    msg = message.payload.decode('utf-8')
                except UnicodeDecodeError as _:
                    msg = "couldn't decode message"
                #if message.topic.matches('tele/+/STATE'):

                if message.topic.matches('stat/+/RESULT'):
                    name = message.topic.value.split('/')[1]
                    #self.query_one(RichLog).write(f"FOUND BUTTON, {t},  {message.topic.value} {self.buttonlist}") 
                    if name not in self.buttonlist:
                        self.add_button(name)
                        self.query_one(RichLog).write(f"FOUND BUTTON, {t},  {message.topic.value} {self.buttonlist}") 
                elif  message.topic.matches('tele/+/STATE'):
                    name = message.topic.value.split('/')[1]
                    if name not in self.buttonlist:
                        self.add_button(name)
                        self.query_one(RichLog).write(f"FOUND BUTTON, {t},  {message.topic.value} {self.buttonlist}") 

                    
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