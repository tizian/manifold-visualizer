import copy, time
from misc import *
from path import *
from draw import *
from mode import Mode
from knob import DraggableKnob
from nanogui import *

class SpecularManifoldSamplingMode(Mode):
    def __init__(self, viewer):
        super().__init__(viewer)

        self.seed_path = None
        self.solution_path = None
        self.intermediate_paths = None

        self.sms_mode = False
        self.seed_paths = []
        self.solution_paths = []
        self.rough_mode = False

        self.constraint_type = ConstraintType.HalfVector
        self.strategy_type = StrategyType.SMS

        self.dragging_start = False
        self.dragging_end   = False
        self.dragging_spec  = False
        self.knob_start = DraggableKnob()
        self.knob_end   = DraggableKnob()

        self.animating = False
        self.time = 0.0
        self.scene = None
        self.n_bounces = 1

        self.last_time = time.time()
        self.animation_state = 0

    def enter(self, last):
        super().enter(last)
        self.viewer.scene_selection_cb(6)

    def scene_changed(self):
        scene = self.viewer.scenes[self.viewer.scene_idx]
        self.n_bounces = scene.n_bounces_default

    def update(self, input, scene):
        super().update(input, scene)
        self.scene = scene

        current_time = time.time()
        dt = current_time - self.last_time
        self.last_time = current_time
        if self.animating:
            self.time += dt

        def sin_wave(t, a, b):
            amplitude = 0.5*(b - a)
            mean = 0.5*(a + b)
            return amplitude*np.sin(2*np.pi*t)+mean

        def within(t, a, b):
            return a < t and t < b, (t - a) / (b - a)

        # int1, t1 = within(self.time, 0.0, 2.0)
        # int2, t2 = within(self.time, 2.3, 4.3)
        # int3, t3 = within(self.time, 4.6, 10.6)

        int1, t1 = within(self.time, 0.0, 3.0)

        if int1:
            scene.spec_u_current = sin_wave(t1, 0.2, 0.8)
        # elif int2:
        #     scene.end_u_current = sin_wave(t2, 0.2, 0.8)
        # elif int3:
        #     scene.spec_u_current = sin_wave(t3, 0.3, 0.7)

        # if self.animating:
        #     self.time += dt
        #     time_p = 0.5 + 0.5*np.sin(0.7*self.time)

        #     scene.spec_u_current = lerp(time_p, 0.1, 0.9)

        # Set positions and update for all three knobs
        p_start = scene.sample_start_position(scene.start_u_current).p
        p_end = scene.sample_end_position(scene.end_u_current).p
        p_spec = scene.sample_spec_position(scene.spec_u_current).p
        self.knob_start.p = copy.copy(p_start)
        self.knob_end.p = copy.copy(p_end)

        self.knob_start.update(input)
        if input.click and (self.knob_start.drag_possible or self.dragging_start):
            self.dragging_start = True
            p_start += input.mouse_dp
        else:
            self.dragging_start = False
        u_proj = scene.start_shape().project(p_start)
        scene.start_u_current = u_proj

        self.knob_end.update(input)
        if input.click and (self.knob_end.drag_possible or self.dragging_end):
            self.dragging_end = True
            p_end += input.mouse_dp
        else:
            self.dragging_end = False
        u_proj = scene.end_shape().project(p_end)
        scene.end_u_current = u_proj

        self.seed_path = scene.sample_mnee_seed_path()
        if self.seed_path.has_specular_segment():
            self.solution_path, self.intermediate_paths = self.newton_solver(scene, self.seed_path)

    def newton_solver(self, scene, seed_path):
        current_path = seed_path.copy()
        intermediate_paths = [current_path]

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

            # Check for success
            converged = True
            for vtx in current_path:
                if vtx.shape.type == Shape.Type.Reflection or vtx.shape.type == Shape.Type.Refraction:
                    if abs(vtx.C) > threshold:
                        converged = False
                        break
            if converged:
                success = True
                break

            proposed_offsets = current_path.copy_positions()
            for k, vtx in enumerate(current_path):
                if vtx.shape.type == Shape.Type.Reflection or vtx.shape.type == Shape.Type.Refraction:
                    proposed_offsets[k] -= self.step_size_scale()*beta * vtx.dp_du * vtx.dX

            # Ray trace to re-project onto specular manifold
            proposed_path = scene.reproject_path_sms(proposed_offsets, current_path, self.n_bounces)
            if not current_path.same_submanifold(proposed_path):
                beta = 0.5 * beta
            else:
                beta = min(1.0, 2*beta)
                current_path = proposed_path
                intermediate_paths.append(current_path)

            i = i + 1
        if success:
            solution_path = current_path
        else:
            solution_path = None
        return solution_path, intermediate_paths

    def draw(self, ctx, scene):
        super().draw(ctx, scene)
        s = scene.scale

        # Filter out first and last path from intermediate steps
        intermediate_paths = []
        if len(self.intermediate_paths) > 2:
            intermediate_paths = self.intermediate_paths[1:-1]
        N = len(intermediate_paths)

        if self.animation_state >= 3:
            draw_dotted_path_lines(ctx, self.seed_path, s, spacing=0.02)
        if self.solution_path and self.animation_state >= 4+N:
            draw_path_lines(ctx, self.solution_path, '', s)

        for k, path in enumerate(intermediate_paths):
            if self.animation_state == 4+k and k < N:
                draw_path_lines(ctx, path, '', s)

        scene.draw(ctx)

        # if self.solution_path and self.animation_state >= 4:
        #     for k, vtx in enumerate(self.solution_path):
        #         if vtx.shape.type == Shape.Type.Reflection or vtx.shape.type == Shape.Type.Refraction:
        #             draw_arrow(ctx, vtx.p, vtx.n, nvg.RGB(255, 0, 0), scale=s, length=0.2)




        if self.animation_state >= 3:
            draw_path_vertices(ctx, self.seed_path, '', s)
        if self.solution_path and self.animation_state >= 4+N:
            draw_path_vertices(ctx, self.solution_path, '', s)

        for k, path in enumerate(intermediate_paths):
            if self.animation_state == 4+k and k < N:
                draw_path_vertices(ctx, path, '', s)

        if self.animation_state >= 1:
            self.knob_start.draw(ctx)
        if self.animation_state >= 2:
            self.knob_end.draw(ctx)

    def layout(self, window):
        return [], []

    def keyboard_event(self, key, scancode, action, modifiers):
        super().keyboard_event(key, scancode, action, modifiers)

        if key == glfw.KEY_RIGHT and action == glfw.PRESS:
            self.animating = not self.animating
            return True

        if key == glfw.KEY_UP and action == glfw.PRESS:
            self.animation_state += 1
            return True

        if key == glfw.KEY_DOWN and action == glfw.PRESS:
            if self.animation_state > 0:
                self.animation_state -= 1
            return True

    def max_steps(self):
        return 20

    def eps_threshold(self):
        return 1e-3

    def step_size_scale(self):
        return 1.0