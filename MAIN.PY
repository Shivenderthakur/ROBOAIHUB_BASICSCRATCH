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
import random

# Inline KV
KV = '''
<Block>:
    # Enable dragging anywhere on the button
    drag_rectangle: self.x, self.y, self.width, self.height
    drag_distance: 0
    drag_timeout: 1000000

<MainWidget>:
    hand: hand_img
    Image:
        id: hand_img
        source: 'hand.png'
        size_hint: None, None
        size: 150, 150
        pos_hint: {'center_x': 0.5, 'center_y': 0.5}

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
        orientation: 'vertical'
        size_hint: None, None
        size: 120, 400
        pos_hint: {'right': 0.98, 'center_y': 0.5}
        spacing: 20
        padding: 10
        Block:
            id: block_forward
            text: 'FORWARD'
            size_hint_y: None
            height: 60
        Block:
            id: block_right
            text: 'RIGHT'
            size_hint_y: None
            height: 60
        Block:
            id: block_left
            text: 'LEFT'
            size_hint_y: None
            height: 60
        Block:
            id: block_backward
            text: 'BACKWARD'
            size_hint_y: None
            height: 60
'''
Builder.load_string(KV)

DIRECTIONS = ['forward', 'right', 'left', 'backward']

class TargetCircle(Widget):
    pass

class Block(DragBehavior, Button):
    """A draggable block representing a direction."""
    direction = None
    def move_to(self, pos, callback=None):
        # Animate block snapping to position
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
        self.targets = {
            'forward': self.ids['target_forward'],
            'right': self.ids['target_right'],
            'left': self.ids['target_left'],
            'backward': self.ids['target_backward']
        }
        for d in DIRECTIONS:
            blk = self.ids[f'block_{d}']
            blk.direction = d
            self.blocks.append(blk)
            blk.bind(on_touch_up=self.on_block_release)

    def animate_hand(self, direction):
        target = self.targets[direction]
        orig = self.hand.center
        anim_out = Animation(center=target.center, duration=0.3)
        anim_back = Animation(center=orig, duration=0.3)
        anim_out.bind(on_complete=lambda *a: anim_back.start(self.hand))
        anim_out.start(self.hand)

    def on_block_release(self, block, touch):
        if block.collide_point(*touch.pos):
            for direction, target in self.targets.items():
                if target.collide_point(*touch.pos):
                    block.move_to(target.center)
                    self.store[direction] = block.text
                    print(f"Stored: {block.text} dropped on {direction.upper()}")
                    return

class RoboAIApp(App):
    def build(self):
        return MainWidget()

if __name__ == '__main__':
    RoboAIApp().run()
