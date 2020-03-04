import copy
from misc import *
from path import *
from draw import *
from mode import Mode
from knob import DraggableKnob
from nanogui import *

class RaytracingMode(Mode):
    def __init__(self, viewer):
        super().__init__(viewer)

        self.path = []

        self.dragging_start = False
        self.dragging_end = False
        self.knob_start = DraggableKnob()

    def update(self, input, scene):
        super().update(input, scene)

        # Sample a new path from start pos & ang
        self.path = scene.sample_path()
        start_vtx = self.path[0]

        # Update start knob
        self.knob_start.p = copy.copy(start_vtx.p)
        self.knob_start.angle = scene.start_angle_current
        self.knob_start.update(input)

        directional = input.alt
        self.knob_start.directional = directional

        if not directional:
            start_shape = start_vtx.shape
            p = copy.copy(self.knob_start.p)
            if input.click and (self.knob_start.drag_possible or self.dragging_start):
                self.dragging_start = True
                p += input.mouse_dp
            else:
                self.dragging_start = False

            u_proj = start_shape.project(p)
            scene.start_u_current = u_proj

        if directional:
            if input.click and (self.knob_start.drag_possible or self.dragging_start):
                self.dragging_start = True
                delta = input.mouse_p - input.mouse_p_click
                angle = np.arctan2(delta[1], delta[0])
                scene.start_angle_current = np.degrees(angle)
            else:
                self.dragging_start = False

    def draw(self, ctx, scene):
        super().draw(ctx, scene)
        s = scene.scale

        draw_path_lines(ctx, self.path, '', s)
        scene.draw(ctx)
        if self.display_tangents_btn.pushed():
            draw_path_tangents(ctx, self.path, s)
        if self.display_normals_btn.pushed():
            draw_path_normals(ctx, self.path, scale=s)
        draw_path_vertices(ctx, self.path, '', s)

        self.knob_start.draw(ctx)

    def layout(self, window):
        toggle_tools = Widget(window)
        toggle_tools.set_layout(BoxLayout(Orientation.Horizontal,
                                          Alignment.Middle, 0, 3))
        Label(toggle_tools, "Display local frame: ")
        self.display_normals_btn = Button(toggle_tools, "", icons.FA_ARROW_UP)
        self.display_normals_btn.set_pushed(True)
        self.display_normals_btn.set_flags(Button.Flags.ToggleButton)
        self.display_tangents_btn = Button(toggle_tools, "", icons.FA_ARROW_RIGHT)
        self.display_tangents_btn.set_flags(Button.Flags.ToggleButton)

        return [toggle_tools], []