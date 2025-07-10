# main.py
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.properties import ObjectProperty
from kivy.uix.behaviors import DragBehavior
from kivy.lang import Builder
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.camera import Camera
import random

# Inline KV
KV = '''
<Block>:
    drag_rectangle: self.x, self.y, self.width, self.height
    drag_distance: 0
    drag_timeout: 1000000

<MainWidget>:
    hand: hand_img
    BoxLayout:
        orientation: 'vertical'
        padding: 10
        spacing: 10
        FloatLayout:
            size_hint_y: 0.8
            Image:
                id: hand_img
                source: 'hand.png'
                size_hint: None, None
                size: 150, 150
                pos_hint: {'center_x': 0.5, 'center_y': 0.5}
            # targets...
            Button:
                id: target_forward
                size_hint: None, None
                size: 120, 120
                pos_hint: {'center_x': 0.5, 'center_y': 0.75}
                background_color: (0.4, 0.7, 1, 1)
                text: 'UP'
                border: (60,60,60,60)
            Button:
                id: target_backward
                size_hint: None, None
                size: 120, 120
                pos_hint: {'center_x': 0.5, 'center_y': 0.25}
                background_color: (1, 0.6, 0.4, 1)
                text: 'DOWN'
                border: (60,60,60,60)
            Button:
                id: target_left
                size_hint: None, None
                size: 120, 120
                pos_hint: {'center_x': 0.25, 'center_y': 0.5}
                background_color: (0.6, 1, 0.4, 1)
                text: 'LEFT'
                border: (60,60,60,60)
            Button:
                id: target_right
                size_hint: None, None
                size: 120, 120
                pos_hint: {'center_x': 0.75, 'center_y': 0.5}
                background_color: (1, 0.4, 0.7, 1)
                text: 'RIGHT'
                border: (60,60,60,60)
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: 0.2
            spacing: 10
            # palette of blocks
            BoxLayout:
                orientation: 'horizontal'
                size_hint_x: None
                width: 500
                spacing: 10
                padding: 5
                Block:
                    id: block_forward
                    text: 'FORWARD'
                    size_hint: None, None
                    size: 100, 60
                Block:
                    id: block_right
                    text: 'RIGHT'
                    size_hint: None, None
                    size: 100, 60
                Block:
                    id: block_left
                    text: 'LEFT'
                    size_hint: None, None
                    size: 100, 60
                Block:
                    id: block_backward
                    text: 'BACKWARD'
                    size_hint: None, None
                    size: 100, 60
            Button:
                id: next_btn
                text: 'Next Window'
                size_hint: None, None
                size: 150, 60
                on_release: root.open_next_window()
'''
Builder.load_string(KV)

DIRECTIONS = ['forward', 'right', 'left', 'backward']

class Block(DragBehavior, Button):
    direction = None
    def move_to(self, pos):
        anim = Animation(center=pos, duration=0.2)
        anim.start(self)

class MainWidget(FloatLayout):
    hand = ObjectProperty(None)
    targets = {}
    blocks = []
    store = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self.setup, 0)

    def setup(self, dt):
        self.targets = {d: self.ids[f'target_{d}'] for d in DIRECTIONS}
        for d in DIRECTIONS:
            blk = self.ids[f'block_{d}']
            blk.direction = d
            self.blocks.append(blk)
            blk.bind(on_touch_up=self.on_block_release)

    def on_block_release(self, block, touch):
        if block.collide_point(*touch.pos):
            for direction, target in self.targets.items():
                if target.collide_point(*touch.pos):
                    block.move_to(target.center)
                    self.store[len(self.store)] = (block.text, direction)
                    print(f"Stored: {block.text} -> {direction.upper()}")
                    return

    def open_next_window(self):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        content.add_widget(Label(text='Hello!'))
        try:
            cam = Camera(play=True, resolution=(640, 480), size_hint=(1, 1))
        except Exception as e:
            cam = Label(text='Camera not available')
            print(f"Camera error: {e}")
        content.add_widget(cam)
        popup = Popup(title='Next Window', content=content, size_hint=(0.8, 0.8))
        popup.open()

class RoboAIApp(App):
    def build(self):
        return MainWidget()

if __name__ == '__main__':
    RoboAIApp().run()
