# main.py
import cv2
import mediapipe as mp
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.behaviors import DragBehavior
from kivy.lang import Builder

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

        FloatLayout:
            id: config_area
            Button:
                id: tgt_up
                text: root.display.get('up', 'UP')
                size_hint: None, None
                size: 130, 130
                pos_hint: {'center_x': 0.5, 'center_y': 0.85}
            Button:
                id: tgt_down
                text: root.display.get('down', 'DOWN')
                size_hint: None, None
                size: 130, 130
                pos_hint: {'center_x': 0.5, 'center_y': 0.15}
            Button:
                id: tgt_left
                text: root.display.get('left', 'LEFT')
                size_hint: None, None
                size: 130, 130
                pos_hint: {'center_x': 0.15, 'center_y': 0.5}
            Button:
                id: tgt_right
                text: root.display.get('right', 'RIGHT')
                size_hint: None, None
                size: 130, 130
                pos_hint: {'center_x': 0.85, 'center_y': 0.5}

        BoxLayout:
            size_hint_y: 0.3
            padding: 10
            spacing: 10
            orientation: 'horizontal'

            BoxLayout:
                orientation: 'horizontal'
                spacing: 10
                Block:
                    id: block_forward
                    text: 'FORWARD'
                Block:
                    id: block_left
                    text: 'LEFT'
                Block:
                    id: block_right
                    text: 'RIGHT'
                Block:
                    id: block_backward
                    text: 'BACKWARD'

            Button:
                text: 'Start'
                size_hint_x: None
                width: 120
                background_color: 0.1, 0.7, 0.2, 1
                on_release: root.start_tracking()

<TrackScreen>:
    BoxLayout:
        orientation: 'vertical'
        Button:
            text: 'Stop Tracking'
            size_hint_y: None
            height: 50
            on_release: root.stop_tracking()
'''

Builder.load_string(KV)

DIRECTIONS = ['up', 'down', 'left', 'right']
DEFAULT = 'DEFAULT'

class Block(DragBehavior, Button):
    pass

class ConfigScreen(Screen):
    display = {}

    def on_pre_enter(self):
        self.display.clear()
        for d in DIRECTIONS:
            self.ids[f'tgt_{d}'].text = d.upper()

    def on_touch_up(self, touch):
        super().on_touch_up(touch)
        for blk_name, tgt_key in [
            ('block_forward', 'up'),
            ('block_backward', 'down'),
            ('block_left', 'left'),
            ('block_right', 'right'),
        ]:
            blk = self.ids.get(blk_name)
            if blk and blk.collide_point(*touch.pos):
                for tgt in DIRECTIONS:
                    btn = self.ids[f'tgt_{tgt}']
                    if btn.collide_point(*touch.pos):
                        self.display[tgt] = blk.text
                        btn.text = blk.text
                        return

    def start_tracking(self):
        from threading import Thread
        from functools import partial
        track_screen = self.manager.get_screen('track')
        track_screen.display = self.display.copy()
        thread = Thread(target=partial(start_video, track_screen.display))
        thread.start()
        self.manager.current = 'track'

class TrackScreen(Screen):
    display = {}

    def stop_tracking(self):
        App.get_running_app().stop()

class RoboAIApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(ConfigScreen(name='config'))
        sm.add_widget(TrackScreen(name='track'))
        return sm


def start_video(display):
    mp_hands = mp.solutions.hands.Hands(min_detection_confidence=0.7)
    cap = cv2.VideoCapture(0)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = mp_hands.process(image_rgb)

        h, w, _ = frame.shape
        movement = 'Center'

        x_min, x_max = int(w * 0.35), int(w * 0.65)
        y_min, y_max = int(h * 0.35), int(h * 0.65)
        cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (255,255,0), 2)

        if results.multi_hand_landmarks:
            lm = results.multi_hand_landmarks[0].landmark[8]
            x_px, y_px, z = int(lm.x * w), int(lm.y * h), lm.z
            cv2.circle(frame, (x_px, y_px), 8, (0,255,0), -1)
            if x_px < x_min:
                movement = 'Left'
            elif x_px > x_max:
                movement = 'Right'
            if y_px < y_min:
                movement = 'Up'
            elif y_px > y_max:
                movement = 'Down'
            if abs(z) > 0.2:
                movement = 'Forward' if z < -0.2 else 'Backward'
            mp.solutions.drawing_utils.draw_landmarks(
                frame, results.multi_hand_landmarks[0], mp.solutions.hands.HAND_CONNECTIONS)

        up_cmd = display.get('up', DEFAULT)
        down_cmd = display.get('down', DEFAULT)
        left_cmd = display.get('left', DEFAULT)
        right_cmd = display.get('right', DEFAULT)

        cv2.putText(frame, up_cmd, (w//2 - 50, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
        cv2.putText(frame, down_cmd, (w//2 - 70, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
        cv2.putText(frame, left_cmd, (20, h//2), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
        cv2.putText(frame, right_cmd, (w - 150, h//2), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)

        cv2.imshow("Robo AI Feed", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    RoboAIApp().run()