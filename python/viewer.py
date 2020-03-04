import gc
import numpy as np

import nanogui
import nanogui.nanovg as nvg
from nanogui import *

import manifolds
from misc import *
from modes.trace_ray import *
from modes.manifold_exploration import *
from modes.specular_manifold_sampling import *
from scenes import create_scenes

class Input:
    def __init__(self, screen):
        self.click = False

        self.alt   = False
        self.shift = False

        self.mouse_p       = np.array([0.0, 0.0])
        self.mouse_dp      = np.array([0.0, 0.0])
        self.mouse_p_click = np.array([0.0, 0.0])

        self.screen = screen

class ManifoldViewer(Screen):
    def __init__(self):
        super(ManifoldViewer, self).__init__((1024, 900), "Manifold 2D Viewer")
        self.set_background(Color(200, 200, 200, 255))

        # Input & view
        self.zoom = 1.0
        self.offset = [0, 0]
        self.input = Input(self)
        self.input.scale = 1.0

        # Scenes
        self.scenes = create_scenes()
        self.scene_idx = 0
        scene = self.scenes[self.scene_idx]
        self.offset = scene.offset
        self.zoom   = scene.zoom

        # Modes
        self.modes = {}
        mode_dicts = [
            (ModeType.TraceRay, TraceRayMode),
            (ModeType.ManifoldExploration, ManifoldExplorationMode),
            (ModeType.SpecularManifoldSampling, SpecularManifoldSamplingMode)
        ]
        for mode, constructor in mode_dicts:
            self.modes[mode] = constructor(self)
            self.modes[mode].mode = mode
        self.mode = ModeType.TraceRay

        # Interface
        self.window = Window(self, "Manifolds")
        self.window.set_position((15, 15))
        self.window.set_layout(GroupLayout())

        ## Scene
        Label(self.window, "Scene selection", "sans-bold")
        scene_tools = Widget(self.window)
        scene_tools.set_layout(BoxLayout(Orientation.Horizontal, Alignment.Middle, 0, 3))
        ### Scene reset
        scene_reset = Button(scene_tools, "", icons.FA_REDO_ALT)
        def scene_reset_cb():
            scene = self.scenes[self.scene_idx]
            scene.start_u_current = scene.start_u_default
            scene.start_angle_current = scene.start_angle_default
            scene.end_u_current = scene.end_u_default
            scene.spec_u_current = scene.spec_u_default
            self.modes[self.mode].scene_reset()
        scene_reset.set_callback(scene_reset_cb)
        scene_reset.set_tooltip("Reset scene")
        self.scene_reset_cb = scene_reset_cb
        ### Scene selection
        scene_selection = ComboBox(scene_tools, [s.name for s in self.scenes])
        scene_selection.set_selected_index(self.scene_idx)
        def scene_selection_cb(idx):
            self.scene_idx = idx
            scene = self.scenes[idx]
            self.offset = scene.offset
            self.zoom   = scene.zoom
            self.modes[self.mode].scene_changed()
        scene_selection.set_callback(scene_selection_cb)
        self.scene_selection_cb = scene_selection_cb

        self.modes[self.mode].enter(0)

        # Options
        Label(self.window, "Options", "sans-bold")
        mode_selection = ComboBox(self.window, [
            "Trace Ray",
            "Manifold Exploration",
            "Specular Manifold Sampling"
        ])
        mode_selection.set_selected_index(self.mode)
        def mode_selection_cb(idx):
            last_mode = self.mode
            self.modes[last_mode].exit(self.modes[idx])
            self.mode = ModeType(idx)
            self.modes[self.mode].enter(self.modes[last_mode])
            for g in self.mode_guis:
                self.window.remove_child(g)
            for w in self.mode_windows:
                self.window.remove_child(w)
            self.mode_guis, self.mode_windows = self.modes[self.mode].layout(self.window)
            self.window.set_fixed_width(350)
            self.perform_layout()
        mode_selection.set_callback(mode_selection_cb)
        self.mode_selection_cb = mode_selection_cb
        self.mode_selection = mode_selection

        self.window.set_fixed_width(350)
        self.perform_layout()

        self.mode_guis = []
        self.mode_windows = []
        mode_selection_cb(self.mode)


    def keyboard_event(self, key, scancode, action, modifiers):
        self.input.shift = False
        self.input.alt   = False
        if action == glfw.PRESS:
            if key == glfw.KEY_LEFT_SHIFT or key == glfw.KEY_RIGHT_SHIFT:
                self.input.shift = True
            elif key == glfw.KEY_LEFT_ALT or key == glfw.KEY_RIGHT_ALT:
                self.input.alt = True

        if super(ManifoldViewer, self).keyboard_event(key, scancode, action, modifiers):
            return True
        if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
            self.set_visible(False)
            return True

        if key == glfw.KEY_SPACE and action == glfw.PRESS:
            print("offset: ", self.offset)
            print("zoom: ", self.zoom)
            print("start_u: ", self.scenes[self.scene_idx].start_u_current)
            print("start_angle: ", self.scenes[self.scene_idx].start_angle_current)
            print("end_u: ", self.scenes[self.scene_idx].end_u_current)
            print("spec_u: ", self.scenes[self.scene_idx].spec_u_current)
            return True

        if key == glfw.KEY_1 and action == glfw.PRESS:
            self.mode_selection_cb(ModeType.TraceRay)
            self.mode_selection.set_selected_index(ModeType.TraceRay)
            return True
        elif key == glfw.KEY_2 and action == glfw.PRESS:
            self.mode_selection_cb(ModeType.ManifoldExploration)
            self.mode_selection.set_selected_index(ModeType.ManifoldExploration)
            return True
        elif key == glfw.KEY_3 and action == glfw.PRESS:
            self.mode_selection_cb(ModeType.SpecularManifoldSampling)
            self.mode_selection.set_selected_index(ModeType.SpecularManifoldSampling)
            return True

        if key == glfw.KEY_R and action == glfw.PRESS:
            self.scene_reset_cb()
            return True

        if key == glfw.KEY_TAB and action == glfw.PRESS:
            self.window.set_visible(not self.window.visible())

        self.modes[self.mode].keyboard_event(key, scancode, action, modifiers)

        return False

    def mouse_motion_event(self, p, rel, button, modifiers):
        if super(ManifoldViewer, self).mouse_motion_event(p, rel, button, modifiers):
            return True

        if button == glfw.MOUSE_BUTTON_2 and self.input.shift:
            self.offset += (0.002/self.zoom) * np.array([rel[0], -rel[1]])

    def mouse_button_event(self, p, button, down, modifiers):
        click = button == 0 and down
        if click:
            self.input.mouse_p_click = self.input.mouse_p

        self.input.click = click

        if super(ManifoldViewer, self).mouse_button_event(p, button, down, modifiers):
            return True

    def scroll_event(self, p, rel):
        if not super(ManifoldViewer, self).scroll_event(p, rel) and self.input.shift:
            v = rel[1] if rel[1] != 0 else rel[0]
            self.zoom += v * 0.1
            self.zoom = min(2.0, max(0.01, self.zoom))

        return True

    def draw(self, ctx):
        if self.mode == ModeType.TraceRay:
            self.set_caption("Manifold 2D Visualization - Trace Ray")
        elif self.mode == ModeType.ManifoldExploration:
            self.set_caption("Manifold 2D Visualization - Manifold Exploration")
        elif self.mode == ModeType.SpecularManifoldSampling:
            self.set_caption("Manifold 2D Visualization - Specular Manifold Sampling")
        else:
            self.set_caption("Manifold 2D Visualization")

        # Setup view transform
        size = self.size()
        aspect = size[1] / size[0]

        ctx.Scale(size[0], size[0])
        ctx.Translate(+0.5, +0.5*aspect)
        ctx.Scale(0.5, -0.5)
        ctx.Scale(self.zoom, self.zoom)
        ctx.Translate(self.offset[0], self.offset[1])
        mvp = ctx.CurrentTransform()
        mvp = np.array([
            [mvp[0], mvp[2], mvp[4]],
            [mvp[1], mvp[3], mvp[5]],
            [0, 0, 1],
        ])
        self.mvp = np.linalg.inv(mvp)

        mp = self.mouse_pos()
        mp = self.mvp @ np.array([mp[0], mp[1], 1])
        new_mp = np.array([mp[0], mp[1]])
        self.input.mouse_dp = new_mp - self.input.mouse_p
        self.input.mouse_p = new_mp

        scene = self.scenes[self.scene_idx]
        self.modes[self.mode].update(self.input, scene)
        self.modes[self.mode].draw(ctx, scene)

        self.input.mouse_dp = np.array([0.0, 0.0])
        ctx.ResetTransform()
        super(ManifoldViewer, self).draw(ctx)

if __name__ == "__main__":
    nanogui.init()
    app = ManifoldViewer()
    app.draw_all()
    app.set_visible(True)
    nanogui.mainloop(refresh=10)
    del app
    gc.collect()
    nanogui.shutdown()