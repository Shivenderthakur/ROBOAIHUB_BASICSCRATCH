# main.py
import cv2
import mediapipe as mp
import serial
import time
import serial.tools.list_ports
import winreg
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import DragBehavior
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.lang import Builder
from functools import partial
from threading import Thread
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.core.text import LabelBase


from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, ListProperty

LabelBase.register(name='ComicRelief-Bold', fn_regular='assets/fonts/ComicRelief-Bold.ttf')

class BlockWithIcon(DragBehavior, FloatLayout):
    label = StringProperty("")
    icon = StringProperty("")
    bg_color = ListProperty([0.3, 0.3, 0.3, 1])

    def animate_press(self):
        Animation(scale=0.9, duration=0.1).start(self)

    def animate_release(self):
        Animation(scale=1.0, duration=0.2, t='out_bounce').start(self)
def list_outgoing_bt_ports():
    results = []
    friendly = {}
    base = r"SYSTEM\CurrentControlSet\Services\BTHPORT\Parameters\Devices"
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base)
        for i in range(winreg.QueryInfoKey(key)[0]):
            mac = winreg.EnumKey(key, i)
            sub = winreg.OpenKey(key, mac)
            try:
                raw, _ = winreg.QueryValueEx(sub, 'Name')
                name = raw.decode() if isinstance(raw, bytes) else raw
                friendly[mac.lower()] = name
            except FileNotFoundError:
                pass
    except FileNotFoundError:
        pass
    for p in serial.tools.list_ports.comports():
        hwid = p.hwid or ''
        if 'BTHENUM' not in hwid:
            continue
        frag = hwid.split('&')[-1].split('_')[0].lower()
        if int(frag, 16) == 0:
            continue
        name = friendly.get(frag, p.description or 'BT Device')
        results.append((p.device, f"{p.device} - {name}"))
    return results

def on_touch_down(self, touch):
    if self.collide_point(*touch.pos):
        Animation(scale=0.95, duration=0.1).start(self)
    return super().on_touch_down(touch)

def on_touch_up(self, touch):
    Animation(scale=1.0, duration=0.2, t='out_bounce').start(self)
    return super().on_touch_up(touch)
# KV Layout
KV = """
<Block>:
    drag_rectangle: self.x, self.y, self.width, self.height
    drag_distance: 0
    drag_timeout: 1000000
    size_hint: None, None
    size: 160, 90
    font_size: 20
    color: 1, 1, 1, 1
    canvas.before:
        Color:
            rgba: self.bg_color
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [20]
        # Soft shadow
        Color:
            rgba: (0, 0, 0, 0.1)
        Rectangle:
            pos: self.x + 2, self.y - 2
            size: self.size
    on_press: self.animate_press()
    on_release: self.animate_release()

<BlockWithIcon>:
    drag_rectangle: self.x, self.y, self.width, self.height
    drag_distance: 0
    drag_timeout: 1000000
    size_hint: None, None
    size: 160, 100
    icon: ''
    label: ''
    color: (0.13, 0.13, 0.13, 1)  # #A0D6FF

    canvas.before:
        Color:
            rgba: self.bg_color
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [20]

    Image:
        source: root.icon
        size_hint: None, None
        size: 48, 48
        pos_hint: {'center_x': 0.5, 'top': 1}

    Label:
        text: root.label
        font_size: 16
        bold: True
        color: 1, 1, 1, 1
        pos_hint: {'center_x': 0.5, 'y': 0}
        size_hint: None, None
        size: self.texture_size
<ConfigScreen>:
    canvas.before:
        Color:
            rgba: (0.98, 0.95, 0.85, 1)
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        orientation: 'vertical'
        padding: 30
        spacing: 20

        Label:
            text: 'Scratch Visual Learning'
            font_name: 'ComicRelief-Bold'
            font_size: 36
            color: (0.2, 0.5, 0.7, 1)
            bold: True
            size_hint_y: None
            height: 80

        Image:
            source: 'assets/images/logo.jfif'
            allow_stretch: False
            keep_ratio: True
            size_hint_y: None
            height: 100
            pos_hint: {'center_x': 0.5}

        BoxLayout:
            orientation: 'horizontal'
            spacing: 15
            size_hint_y: None
            height: 60

            Spinner:
                id: port_spinner
                text: 'Choose Device'
                values: []
                font_size: 18
                background_color: (0.95, 0.95, 0.75, 1)
                color: (0.15, 0.15, 0.15, 1)
                border: (16, 16, 16, 16)

            Button:
                text: 'Refresh'
                size_hint_x: None
                width: 120
                font_size: 18
                background_normal: ''
                background_color: (0.6, 0.5, 0.8, 1)
                color: (1, 1, 1, 1)
                on_release: root.refresh_ports()

            Button:
                text: 'Start Magic!'
                size_hint_x: None
                width: 140
                font_size: 18
                background_normal: ''
                background_color: (0.3, 0.7, 0.3, 1)
                color: (1, 1, 1, 1)
                on_release: root.start_tracking()

        FloatLayout:
            Label:
                text: 'Drag the colorful blocks onto arrows'
                font_size: 20
                pos_hint: {'center_x': 0.5, 'top': 1}
                color: (0.3, 0.3, 0.3, 1)

            # Drop targets
            Button:
                id: tgt_up
                text: root.display['up']
                size_hint: None, None
                size: 160, 160
                pos_hint: {'center_x': 0.5, 'center_y': 0.8}
                background_normal: ''
                background_color: (1, 0.9, 0.7, 1)
                color: (0.1, 0.1, 0.1, 1)
                on_release:
                    Animation(size=(180, 180), duration=0.2, t='out_bounce').start(self)

            Button:
                id: tgt_down
                text: root.display['down']
                size_hint: None, None
                size: 160, 160
                pos_hint: {'center_x': 0.5, 'center_y': 0.2}
                background_normal: ''
                background_color: (1, 0.7, 0.9, 1)
                color: (0.1, 0.1, 0.1, 1)
                on_release:
                    Animation(size=(180, 180), duration=0.2, t='out_bounce').start(self)

            Button:
                id: tgt_left
                text: root.display['left']
                size_hint: None, None
                size: 160, 160
                pos_hint: {'center_x': 0.2, 'center_y': 0.5}
                background_normal: ''
                background_color: (0.7, 0.9, 1, 1)
                color: (0.1, 0.1, 0.1, 1)
                on_release:
                    Animation(size=(180, 180), duration=0.2, t='out_bounce').start(self)

            Button:
                id: tgt_right
                text: root.display['right']
                size_hint: None, None
                size: 160, 160
                pos_hint: {'center_x': 0.8, 'center_y': 0.5}
                background_normal: ''
                background_color: (0.9, 1, 0.7, 1)
                color: (0.1, 0.1, 0.1, 1)
                on_release:
                    Animation(size=(180, 180), duration=0.2, t='out_bounce').start(self)

            # Blocks
            BlockWithIcon:
                id: block_forward
                icon: 'assets/icons/forw.png'
                label: 'Forward'
                pos: 20, 20
                bg_color: (0.627,0.839,1,1)

            BlockWithIcon:
                id: block_backward
                icon: 'assets/icons/back.png'
                label: 'Back'
                pos: 180, 20
                bg_color: (0.627,0.839,1,1)

            BlockWithIcon:
                id: block_left
                icon: 'assets/icons/left.png'
                label: 'Left'
                pos: 340, 20
                bg_color: (0.627,0.839,1,1)

            BlockWithIcon:
                id: block_right
                icon: 'assets/icons/right.png'
                label: 'Right'
                pos: 500, 20
                bg_color: (0.627,0.839,1,1)

<TrackScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: 20
        spacing: 20

        Label:
            id: motion_label
            text: 'Movement: NONE'
            font_size: 24
            color: (0.1, 0.3, 0.6, 1)
            size_hint_y: None
            height: 60

        Label:
            id: command_label
            text: 'Command: NONE'
            font_size: 20
            color: (0.6, 0.2, 0.2, 1)
            size_hint_y: None
            height: 50

        Button:
            text: 'Stop & Back'
            font_size: 18
            background_normal: ''
            background_color: (1, 0.5, 0.5, 1)
            color: (1, 1, 1, 1)
            size_hint_y: None
            height: 60
            on_release: root.stop_tracking()
"""

Builder.load_string(KV)

# Supported gestures and directions
DIRECTIONS = ['up', 'down', 'left', 'right', 'forward', 'backward']


# Supported gestures and directions
DIRECTIONS = ['up', 'down', 'left', 'right', 'forward', 'backward']

class Block(DragBehavior, Button):
    bg_color = (0.2, 0.6, 0.8, 1)
    def animate_press(self):
        Animation(size=(self.width*0.9, self.height*0.9), duration=0.1).start(self)
    def animate_release(self):
        Animation(size=(120,60), duration=0.2, t='out_bounce').start(self)

class ConfigScreen(Screen):
    display = {d:d.upper() for d in DIRECTIONS}
    ports = []

    def on_pre_enter(self):
        self.refresh_ports()

    def refresh_ports(self):
        self.ports = list_outgoing_bt_ports()
        spinner = self.ids.port_spinner
        spinner.values = [p[1] for p in self.ports]
        spinner.text = spinner.values[0] if spinner.values else 'No Device'

    def on_touch_up(self, touch):
        super().on_touch_up(touch)
        # detect which block was dragged
        for block_id in ['block_forward', 'block_backward', 'block_left', 'block_right']:
            blk = self.ids.get(block_id)
            if blk and blk.collide_point(*touch.pos):
                # drop onto any target
                for dir_key in ['up','down','left','right']:
                    tgt = self.ids.get(f'tgt_{dir_key}')
                    if tgt and tgt.collide_point(*touch.pos):
                        # assign custom label
                        """self.display[dir_key] = blk.text
                        tgt.text = blk.text"""
                        self.display[dir_key] = blk.label
                        tgt.text = blk.label
                        Animation(size=(160,160), duration=0.1, t='out_quad').start(tgt)
                        return

    def start_tracking(self):
        app = App.get_running_app()
        sel = self.ids.port_spinner.text
        port = next((p[0] for p in self.ports if p[1]==sel), None)
        app.ser = serial.Serial(port,38400) if port else None
        app.display = self.display
        app.tracking_active = True
        app.tracking_thread = Thread(target=partial(track_loop, app.display, app.ser, app), daemon=True)
        app.tracking_thread.start()
        self.manager.current = 'track'

class TrackScreen(Screen):
    def stop_tracking(self):
        app = App.get_running_app()
        app.tracking_active = False
        if app.ser:
            app.ser.close()
        self.manager.current = 'config'

class RoboAIApp(App):
    ser = None
    display = {}
    tracking_active = False
    tracking_thread = None

    def build(self):
        sm = ScreenManager()
        sm.add_widget(ConfigScreen(name='config'))
        sm.add_widget(TrackScreen(name='track'))
        return sm

# Gesture & Serial Loop

def track_loop(display, ser, app):
    hands = mp.solutions.hands.Hands(min_detection_confidence=0.7)
    cap = cv2.VideoCapture(0)
    screen = app.root.get_screen('track')
    last_cmd = None

    while cap.isOpened() and app.tracking_active:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)
        img = frame.copy()
        h, w, _ = frame.shape
        img = frame.copy()
        res = hands.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        mov = 'stop'
        gear = 'GEAR0'
        if res.multi_hand_landmarks:
            hand = res.multi_hand_landmarks[0]
            lm8 = hand.landmark[8]
            x, y, z = int(lm8.x*w), int(lm8.y*h), lm8.z
            if x < w*0.35: mov='left'
            elif x > w*0.65: mov='right'
            if y < h*0.35: mov='up'
            elif y > h*0.65: mov='down'
            if abs(z)>0.2: mov='forward' if z< -0.2 else 'backward'
            count = sum(
                1 for i,tip in enumerate([4,8,12,16,20])
                if (lm:=hand.landmark[tip]) and ((i==0 and lm.x<hand.landmark[tip-2].x) or (i>0 and lm.y<hand.landmark[tip-2].y))
            )
            gear = f'GEAR{count}'
        mapped = display.get(mov, mov.upper())
        cmd = f'{gear},{mapped}'
        if True:
            try:
                ser.write((cmd+';').encode())
                last_cmd = cmd
                Clock.schedule_once(lambda dt: setattr(screen.ids.command_label,'text',f"Sent: {cmd}"))
                
            except Exception as e:
                Clock.schedule_once(lambda dt: setattr(screen.ids.command_label,'text',f"Err: {e}"))
        Clock.schedule_once(lambda dt: setattr(screen.ids.motion_label,'text',f"Movement: {mov.upper()} | {gear}"))
        cv2.putText(img,cmd,(10,40),cv2.FONT_HERSHEY_SIMPLEX,1,(0,255,255),2)
        cv2.imshow('RoboAI',img)
        if cv2.waitKey(1)&0xFF==27: break
    cap.release(); cv2.destroyAllWindows()
    if ser: ser.close()

if __name__=='__main__':
    RoboAIApp().run()

