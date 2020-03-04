import copy
from misc import *
from path import *
from draw import *
from mode import Mode
from knob import DraggableKnob
from nanogui import *

class ManifoldExplorationMode(Mode):
    def __init__(self, viewer):
        super().__init__(viewer)

        self.path = None
        self.tangent_path = None

        self.dragging_start = False
        self.dragging_end = False
        self.knob_start = DraggableKnob()
        self.knob_end   = DraggableKnob()
        self.knob_end.active = False

        self.path_needs_update = True
        self.constraint_type = ConstraintType.HalfVector

        self.positions = []

    def enter(self, last):
        super().enter(last)
        self.path_needs_update = True

    def scene_reset(self):
        super().scene_reset()
        self.path_needs_update = True

    def scene_changed(self):
        super().scene_changed()
        self.path_needs_update = True

    def update(self, input, scene):
        super().update(input, scene)

        self.tangent_path = None

        # Sample a new path from start pos & ang
        if self.path_needs_update:
            self.path = scene.sample_path()
            self.positions = self.path.copy_positions()
            self.path_needs_update = False
        start_vtx = self.path[0]
        end_vtx   = self.path[-1]

        self.path.compute_tangent_derivatives(self.constraint_type)

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
                self.path_needs_update = True
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
                self.path_needs_update = True
            else:
                self.dragging_start = False

        valid_path = self.path.has_specular_segment()

        old_position = copy.copy(self.positions[-1])

        # Update end knob
        self.knob_end.active = valid_path
        if valid_path:
            self.knob_end.update(input)
            if input.click and (self.knob_end.drag_possible or self.dragging_end):
                self.dragging_end = True

                # Adjust endpoint based on mouse movement
                dp = input.mouse_dp
                self.positions[-1] += dp
            else:
                self.dragging_end = False

            if self.dragging_end:
                end_shape = self.path[-1].shape
                t_proj = end_shape.project(self.positions[-1])
                self.positions[-1] = end_shape.sample_position(t_proj).p

            new_position = copy.copy(self.positions[-1])

            if self.tangents_btn.pushed():
                ## TANGENT MODE

                # Convert spatial offset of endpoint into tangential offset (along u)
                du = self.path[-1].s @ (self.positions[-1] - old_position)

                # Update path vertices (to first order) based on endpoint movement
                for idx in range(1, len(self.positions)-1):
                    self.positions[idx] -= 1.0 * self.path[idx].dp_du * self.path[idx].dC_duk * du

                self.tangent_path = scene.reproject_path_me(self.positions)
            else:
                ## FULL MANIFOLD WALK MODE
                new_position = copy.copy(self.positions[-1])

                # Try to walk from start to end position
                dx = new_position - old_position
                current_path = self.path.copy()

                if norm(dx) > 0:
                    i = 0
                    beta = 1.0
                    N = self.max_steps()
                    threshold = self.eps_threshold()
                    success = False
                    while True:
                        # Give up after too many iterations
                        if i >= N:
                            break

                        # Compute tangents and constraints
                        current_path.compute_tangent_derivatives(self.constraint_type)
                        if current_path.singular:
                            break

                        # Convert spatial offset of endpoint into tangential offset (along u)
                        du = current_path[-1].s @ dx

                        # And move first specular vertex in chain according to it
                        offset_positions = current_path.copy_positions()
                        offset_positions[1] -= beta * current_path[1].dp_du * current_path[1].dC_duk * du

                        # Ray trace to re-project onto specular manifold
                        proposed_path = scene.reproject_path_me(offset_positions)
                        if not current_path.same_submanifold(proposed_path):
                            beta = 0.5 * beta
                            i += 1
                            continue

                        # Check for forward progress
                        if proposed_path:
                            delta_old = norm(new_position -  current_path[-1].p)
                            delta_new = norm(new_position - proposed_path[-1].p)
                            if delta_new < delta_old:
                                beta = min(1.0, 2*beta)
                                current_path = proposed_path
                            else:
                                beta = 0.5 * beta
                        else:
                            beta = 0.5 * beta

                        i += 1

                        # Check for success
                        dx = new_position - current_path[-1].p
                        if norm(dx) < threshold:
                            success = True
                            break

                    if success:
                        self.path = current_path
                    else:
                        self.positions[-1] = old_position

                    # Update start angle s.t. we can move start point without "jump" in visualization
                    new_start_dir   = normalize(self.path[1].p - self.path[0].p)
                    new_start_angle = np.arctan2(new_start_dir[1], new_start_dir[0])
                    scene.start_angle_current = np.degrees(new_start_angle)

        self.knob_end.p = self.positions[-1]

    def draw(self, ctx, scene):
        super().draw(ctx, scene)
        s = scene.scale

        draw_path_lines(ctx, self.path, '', s)
        scene.draw(ctx)
        if self.display_tangents_btn.pushed():
            draw_path_tangents(ctx, self.path, s)
        if self.display_normals_btn.pushed():
            draw_path_normals(ctx, self.path, scale=s)

        if self.tangent_path and self.tangents_btn.pushed() and self.tangents_path_btn.pushed():
            draw_path_lines(ctx, self.tangent_path, modifier='tangent', scale=s)

        draw_path_vertices(ctx, self.path, '', s)
        if self.tangents_btn.pushed() and self.path.has_specular_segment():
            draw_vertices(ctx, self.positions[1:-1], nvg.RGB(255, 0, 0), 1.3*s)

        self.knob_start.draw(ctx)
        self.knob_end.draw(ctx)

    def layout(self, window):
        frame_tools = Widget(window)
        frame_tools.set_layout(BoxLayout(Orientation.Horizontal,
                                          Alignment.Middle, 0, 3))
        Label(frame_tools, "Display local frame: ")
        self.display_normals_btn = Button(frame_tools, "", icons.FA_ARROW_UP)
        self.display_normals_btn.set_pushed(True)
        self.display_normals_btn.set_flags(Button.Flags.ToggleButton)
        self.display_tangents_btn = Button(frame_tools, "", icons.FA_ARROW_RIGHT)
        self.display_tangents_btn.set_flags(Button.Flags.ToggleButton)

        constraint_tools = Widget(window)
        constraint_tools.set_layout(BoxLayout(Orientation.Horizontal,
                                      Alignment.Middle, 0, 3))
        Label(constraint_tools, "Constraint type: ")

        self.constraint_hv_btn = Button(constraint_tools, "", icons.FA_RULER_COMBINED)
        self.constraint_hv_btn.set_flags(Button.Flags.RadioButton)
        self.constraint_hv_btn.set_pushed(self.constraint_type == ConstraintType.HalfVector)
        def constraint_hv_cb(state):
            if state:
                self.constraint_type = ConstraintType.HalfVector
        self.constraint_hv_btn.set_change_callback(constraint_hv_cb)

        self.constraint_dir_btn = Button(constraint_tools, "", icons.FA_DRAFTING_COMPASS)
        self.constraint_dir_btn.set_flags(Button.Flags.RadioButton)
        self.constraint_dir_btn.set_pushed(self.constraint_type == ConstraintType.AngleDifference)
        def constraint_dir_cb(state):
            if state:
                self.constraint_type = ConstraintType.AngleDifference
        self.constraint_dir_btn.set_change_callback(constraint_dir_cb)

        tangent_tools = Widget(window)
        tangent_tools.set_layout(BoxLayout(Orientation.Horizontal,
                                      Alignment.Middle, 0, 3))
        Label(tangent_tools, "Toggle tangent steps: ")
        self.tangents_btn = Button(tangent_tools, "", icons.FA_RULER)
        self.tangents_btn.set_pushed(False)
        self.tangents_btn.set_flags(Button.Flags.ToggleButton)
        def tangents_mode_cb(state):
            self.positions = self.path.copy_positions()
            if not self.tangents_btn.pushed():
                self.tangents_path_btn.set_pushed(False)
        self.tangents_btn.set_change_callback(tangents_mode_cb)

        self.tangents_path_btn = Button(tangent_tools, "", icons.FA_SLASH)
        self.tangents_path_btn.set_pushed(False)
        self.tangents_path_btn.set_flags(Button.Flags.ToggleButton)

        self.debug_btn = Button(window, "Debug print", icons.FA_SPIDER)
        def debug_cb():
            self.path.print_derivative_debug(1, self.constraint_type)
        self.debug_btn.set_callback(debug_cb)

        steps_eps_tools = Widget(window)
        steps_eps_tools.set_layout(BoxLayout(Orientation.Horizontal,
                                             Alignment.Middle, 0, 3))

        Label(steps_eps_tools, "N")
        self.max_steps_sl = Slider(steps_eps_tools)
        max_steps_tb = TextBox(steps_eps_tools)
        max_steps_tb.set_value("20")
        max_steps_tb.set_font_size(20)
        max_steps_tb.set_alignment(TextBox.Alignment.Right)

        self.max_steps_sl.set_value(0.3878)
        def max_steps_cb(value):
            max_steps_tb.set_value("%i" % (1 + int(49*value)))
        self.max_steps_sl.set_callback(max_steps_cb)


        Label(steps_eps_tools, "eps")
        self.eps_sl = Slider(steps_eps_tools)
        eps_tb = TextBox(steps_eps_tools)
        eps_tb.set_value("1.0E-03")
        eps_tb.set_font_size(20)
        eps_tb.set_alignment(TextBox.Alignment.Right)

        self.eps_sl.set_value(0.285)
        def eps_cb(value):
            eps_tb.set_value("%.1E" % 10.0**(-(1 + value*7)))
        self.eps_sl.set_callback(eps_cb)


        return [frame_tools, constraint_tools, tangent_tools, self.debug_btn, steps_eps_tools], []

    def max_steps(self):
        value = self.max_steps_sl.value()
        return 1 + int(49*value)

    def eps_threshold(self):
        value = self.eps_sl.value()
        return 10.0**(-(1 + value*7))