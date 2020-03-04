import gc
import numpy as np

import ext.nanogui.nanogui as nanogui
import ext.nanogui.nanogui.nanovg as nvg
from ext.nanogui.nanogui import *

import manifolds

def draw_coord_system(ctx):
    ctx.StrokeColor(nvg.RGB(0, 0, 0))
    ctx.StrokeWidth(0.005)

    for i in range(-100, 101):
        ctx.BeginPath()
        ctx.MoveTo(-1000.0, float(i))
        ctx.LineTo(+1000.0, float(i))
        ctx.Stroke()

    for i in range(-100, 101):
        ctx.BeginPath()
        ctx.MoveTo(float(i), -1000.0)
        ctx.LineTo(float(i), +1000.0)
        ctx.Stroke()

    ctx.StrokeWidth(0.01)

    ctx.BeginPath()
    ctx.MoveTo(-1000.0, 0.0)
    ctx.LineTo(+1000.0, 0.0)
    ctx.Stroke()

    ctx.BeginPath()
    ctx.MoveTo(0.0, -1000.0)
    ctx.LineTo(0.0, +1000.0)
    ctx.Stroke()

def draw_vertex(ctx, vtx):
    ctx.FillColor(nvg.RGB(0, 0, 0))
    ctx.BeginPath()
    ctx.Circle(vtx.p[0], vtx.p[1], 0.02)
    ctx.Fill()

def draw_normal(ctx, vtx, scale=1.0):
    p0 = vtx.p
    theta = np.arctan2(vtx.n[1], vtx.n[0])
    p1 = p0 + vtx.n * 0.08 * scale

    ctx.Save()
    ctx.StrokeWidth(0.01)

    ctx.BeginPath()
    ctx.MoveTo(p0[0], p0[1])
    ctx.LineTo(p1[0], p1[1])
    ctx.Stroke()

    ctx.Restore()

    n_a = np.array([np.cos(theta+0.3), np.sin(theta+0.3)])
    n_b = np.array([np.cos(theta-0.3), np.sin(theta-0.3)])
    p_a = p0 + n_a * 0.07 * scale
    p_b = p0 + n_b * 0.07 * scale
    p_tip = p1 + vtx.n * 0.03 * scale

    ctx.BeginPath()
    ctx.MoveTo(p_tip[0], p_tip[1])
    ctx.LineTo(p_a[0], p_a[1])
    ctx.ArcTo(p1[0], p1[1], p_b[0], p_b[1], 0.03)
    ctx.LineTo(p_b[0], p_b[1])
    ctx.LineTo(p_tip[0], p_tip[1])
    ctx.Fill()

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
        self.set_background(Color(150, 150, 150, 255))
        self.time = 0.0

        # Input & view
        self.zoom = 1.0
        self.offset = [0, 0]
        self.input = Input(self)
        self.input.scale = 1.0

        # Interface
        self.window = Window(self, "Manifolds")
        self.window.set_position((15, 15))
        self.window.set_layout(GroupLayout())

        # Scene
        # self.shape = manifolds.Circle([0, 0], 0.8)
        self.shape = manifolds.CircleSegment([-0.5, 0.5], [0.8, 0], 3.0)
        # self.shape.flip()
        self.shape.type = manifolds.Shape.Type.Reflection

        self.perform_layout()

    def keyboard_event(self, key, scancode, action, modifiers):
        self.input.shift = modifiers == 1
        self.input.alt   = modifiers == 4

        if super(ManifoldViewer, self).keyboard_event(key, scancode, action, modifiers):
            return True
        if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
            self.set_visible(False)
            return True

        if key == glfw.KEY_SPACE and action == glfw.PRESS:
            print("offset: ", self.offset)
            print("zoom: ", self.zoom)
            return True

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
        self.time += 0.01

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


        # draw_coord_system(ctx)

        self.shape.draw(ctx, False)
        sample = 0.5*(np.sin(self.time) + 1.0)
        si = self.shape.sample_position(sample)

        draw_vertex(ctx, si)
        draw_normal(ctx, si)

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