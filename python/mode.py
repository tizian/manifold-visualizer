from misc import *

class Mode:
    def __init__(self, viewer):
        self.viewer = viewer
        self.scene  = viewer.scenes[viewer.scene_idx]

    def enter(self, last):
        pass

    def exit(self, next):
        pass

    def scene_reset(self):
        pass

    def scene_changed(self):
        pass

    def update(self, input, scene):
        pass

    def draw(self, ctx, scene):
        pass

    def layout(self, window):
        return [], []

    def keyboard_event(self, key, scancode, action, modifiers):
        return False