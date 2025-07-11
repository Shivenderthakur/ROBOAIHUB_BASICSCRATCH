# main.py
import cv2
import mediapipe as mp
import serial
import serial.tools.list_ports
import winreg
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import DragBehavior
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.lang import Builder
from functools import partial
from threading import Thread

# KV layout
KV = '''
<Block>:
    drag_rectangle: self.x, self.y, self.width, self.height
    drag_distance: 0
    drag_timeout: 1000000
    size_hint: None, None
    size: 100, 60
    font_size: 18
    background_color: 0.2, 0.6, 0.8, 1

<ConfigScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: 10
        spacing: 10
        BoxLayout:
            orientation: 'horizontal'
            spacing: 10
            size_hint_y: None
            height: 40
            Button:
                text: 'Start Tracking'
                on_release: root.start_tracking()
        FloatLayout:
            id: config_area
            Button:
                id: tgt_up
                text: root.display.get('up','UP')
                size_hint: None, None
                size: 130, 130
                pos_hint: {'center_x': .5, 'center_y': .85}
            Button:
                id: tgt_down
                text: root.display.get('down','DOWN')
                size_hint: None, None
                size: 130, 130
                pos_hint: {'center_x': .5, 'center_y': .15}
            Button:
                id: tgt_left
                text: root.display.get('left','LEFT')
                size_hint: None, None
                size: 130, 130
                pos_hint: {'center_x': .15, 'center_y': .5}
            Button:
                id: tgt_right
                text: root.display.get('right','RIGHT')
                size_hint: None, None
                size: 130, 130
                pos_hint: {'center_x': .85, 'center_y': .5}
            Block:
                id: block_forward
                text: 'FORWARD'
                pos: (10, 10)
            Block:
                id: block_left
                text: 'LEFT'
                pos: (130, 10)
            Block:
                id: block_right
                text: 'RIGHT'
                pos: (250, 10)
            Block:
                id: block_backward
                text: 'BACKWARD'
                pos: (370, 10)
<TrackScreen>:
    BoxLayout:
        orientation: 'vertical'
        Label:
            id: motion_label
            text: 'Movement: NONE'
            size_hint_y: None
            height: 40
        Button:
            text: 'Stop'
            size_hint_y: None
            height: 40
            on_release: root.stop_tracking()
'''

Builder.load_string(KV)
DIRECTIONS = ['up', 'down', 'left', 'right']
DEFAULT = 'DEFAULT'

# Bluetooth COM discovery
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
        results.append((p.device, name))
    return results

class Block(DragBehavior, Button):
    pass

class ConfigScreen(Screen):
    display = {}
    def on_touch_up(self, touch):
        super().on_touch_up(touch)
        for blk, idkey in [('block_forward', 'up'), ('block_backward', 'down'), ('block_left', 'left'), ('block_right', 'right')]:
            blk_widget = self.ids.get(blk)
            if blk_widget and blk_widget.collide_point(*touch.pos):
                for tgt in DIRECTIONS:
                    btn = self.ids[f'tgt_{tgt}']
                    if btn.collide_point(*touch.pos):
                        self.display[tgt] = blk_widget.text
                        btn.text = blk_widget.text
                        return
    def start_tracking(self):
        ports = list_outgoing_bt_ports()
        port = ports[0][0] if ports else None
        ser = serial.Serial(port, 9600) if port else None
        Thread(target=partial(track_loop, self.display, ser), daemon=True).start()
        self.manager.current = 'track'

class TrackScreen(Screen):
    def stop_tracking(self):
        App.get_running_app().stop()

class RoboAIApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(ConfigScreen(name='config'))
        sm.add_widget(TrackScreen(name='track'))
        return sm

def track_loop(display, ser):
    hands = mp.solutions.hands.Hands(min_detection_confidence=0.7)
    cap = cv2.VideoCapture(0)
    last = None
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        # Removed flip to preserve correct left/right interpretation
        h, w, _ = frame.shape
        img = frame
        res = hands.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        mov = 'center'
        x_min, x_max = int(w * .35), int(w * .65)
        y_min, y_max = int(h * .35), int(h * .65)
        if res.multi_hand_landmarks:
            lm = res.multi_hand_landmarks[0].landmark[8]
            x, y, z = int(lm.x * w), int(lm.y * h), lm.z
            if x < x_min:
                mov = 'right'
            elif x > x_max:
                mov = 'left'
            if y < y_min:
                mov = 'up'
            elif y > y_max:
                mov = 'down'
            if abs(z) > 0.2:
                mov = 'forward' if z < -0.2 else 'backward'
        cmd = display.get(mov.lower(), DEFAULT)
        if ser and cmd != last:
            ser.write(cmd.encode())
            last = cmd
        cv2.putText(img, cmd, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        cv2.imshow('RoboAI', img)
        if cv2.waitKey(1) & 0xFF == 27:
            break
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    RoboAIApp().run()
