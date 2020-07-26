import copy
from misc import *
from path import *
from draw import *
from mode import Mode
from knob import DraggableKnob
from nanogui import *

check_visibility = False

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
        self.knob_spec  = DraggableKnob()

        self.animating = False
        self.time = 0.0
        self.scene = None
        self.animation_state = 0
        self.seed_points = []

    def scene_changed(self):
        scene = self.viewer.scenes[self.viewer.scene_idx]
        self.n_bounces_box.set_value(scene.n_bounces_default)

    def update(self, input, scene):
        super().update(input, scene)
        self.scene = scene

        if self.animating:
            self.time += 0.01
            time_p = 0.5 + 0.5*np.sin(self.time)

            scene.spec_u_current = lerp(time_p, 0.1, 0.9)

        # Set positions and update for all three knobs
        p_start = scene.sample_start_position(scene.start_u_current).p
        p_end = scene.sample_end_position(scene.end_u_current).p
        p_spec = scene.sample_spec_position(scene.spec_u_current).p
        self.knob_start.p = copy.copy(p_start)
        self.knob_end.p = copy.copy(p_end)
        self.knob_spec.p = copy.copy(p_spec)

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

        self.knob_spec.active = self.strategy_type == StrategyType.SMS and not self.sms_mode and not self.rough_mode
        self.knob_spec.update(input)
        if input.click and (self.knob_spec.drag_possible or self.dragging_spec):
            self.dragging_spec = True
            p_spec += input.mouse_dp
        else:
            self.dragging_spec = False
        u_proj = scene.first_specular_shape().project(p_spec)
        scene.spec_u_current = u_proj

        if not self.sms_mode and not self.rough_mode:
            if self.strategy_type == StrategyType.MNEE:
                self.seed_path = scene.sample_mnee_seed_path()
            else:
                self.seed_path = scene.sample_seed_path(self.n_bounces_box.value())

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
            proposed_path = scene.reproject_path_sms(proposed_offsets, current_path, self.n_bounces_box.value())
            if not current_path.same_submanifold(proposed_path):
                beta = 0.5 * beta
            else:
                beta = min(1.0, 2*beta)
                current_path = proposed_path
                intermediate_paths.append(current_path)

            i = i + 1

        if success and check_visibility:
            p_last = current_path[-1].p
            p_spec = current_path[-2].p
            d = p_spec - p_last
            d_norm = norm(d)
            d /= d_norm
            ray = Ray2f(p_last, d, 1e-4, d_norm)
            it = scene.ray_intersect(ray)
            if it.is_valid():
                success = False

        if success:
            solution_path = current_path
        else:
            solution_path = None
        return solution_path, intermediate_paths

    def draw(self, ctx, scene):
        super().draw(ctx, scene)
        s = scene.scale

        show_intermediate_steps = self.show_intermediate_steps_chb.checked()

        if self.sms_mode:
            if self.animation_state == 3:
                for solution in self.solution_paths:
                    draw_path_lines(ctx, solution, '', s)
        elif self.rough_mode:
            draw_dotted_path_lines(ctx, self.seed_path, 0.6*s, spacing=0.02)
            for solution in self.solution_paths:
                draw_intermediate_path_lines(ctx, solution, nvg.RGB(80, 80, 80), s)
            if self.solution_path:
                draw_intermediate_path_lines(ctx, self.solution_path, nvg.RGB(255, 0, 0), s)
        elif not show_intermediate_steps:
            pass
            # draw_dotted_path_lines(ctx, self.seed_path, s, spacing=0.02)
            # if self.solution_path:
            #     draw_path_lines(ctx, self.solution_path, '', s)
        else:
            N = len(self.intermediate_paths)
            g = np.linspace(0, 255, N)
            r = np.linspace(255, 0, N)
            for k, path in enumerate(self.intermediate_paths):
                draw_intermediate_path_lines(ctx, path, nvg.RGB(int(r[k]), int(g[k]), 0), s)

        if not self.sms_mode:
            draw_dotted_path_lines(ctx, self.seed_path, s, spacing=0.02)
            if self.solution_path:
                draw_path_lines(ctx, self.solution_path, '', s)

        scene.draw(ctx)

        if self.sms_mode or self.rough_mode:
            pass
        elif self.show_constraint_chb.checked():
            for k, vtx in enumerate(self.seed_path):
                if vtx.shape.type == Shape.Type.Reflection or vtx.shape.type == Shape.Type.Refraction:
                    vtx_prev = self.seed_path[k-1]
                    vtx_next = self.seed_path[k+1]
                    wo = normalize(vtx_next.p - vtx.p)
                    wi = normalize(vtx_prev.p - vtx.p)

                    eta = self.seed_path[k].shape.eta
                    if dot(wi, self.seed_path[k].n) < 0.0:
                        eta = 1.0/eta

                    if self.constraint_type == ConstraintType.HalfVector:
                        draw_arrow(ctx, vtx.p, vtx.n, nvg.RGB(255, 0, 0), scale=s, length=0.25)

                        h = normalize(wi + eta * wo)
                        if eta != 1.0:
                            h *= -1
                        draw_arrow(ctx, vtx.p, wi, nvg.RGB(0, 0, 0), scale=s, length=0.25)
                        draw_arrow(ctx, vtx.p, wo, nvg.RGB(0, 0, 0), scale=s, length=0.25)
                        draw_arrow(ctx, vtx.p, h, nvg.RGB(0, 128, 0), scale=s, length=0.25)

                        constraint = dot(vtx.s, h)
                        draw_line(ctx, vtx.p, vtx.p+0.25*constraint*vtx.s, nvg.RGB(120, 80, 250), scale=1.2*s, endcap_b=True)
                    elif self.constraint_type == ConstraintType.AngleDifference:
                        if self.flip_constraint_chb.checked():
                            wi, wo = wo, wi

                        m = vtx.s * vtx.n_offset[0] + vtx.n * vtx.n_offset[1]
                        if eta == 1.0:
                            wio = reflect(wi, m)
                        else:
                            wio = refract(wi, m, eta)
                        if wio[0]:
                            wio = wio[1]
                            phi_wo = np.arctan2(wo[1], wo[0])
                            phi_wio = np.arctan2(wio[1], wio[0])
                            draw_arrow(ctx, vtx.p, vtx.n, nvg.RGB(255, 0, 0), scale=s, length=0.25)
                            draw_angle(ctx, vtx.p, 0.2, phi_wo, phi_wio, nvg.RGB(120, 80, 250), scale=1.2*s, flip=(phi_wio - phi_wo < 0))
                            draw_arrow(ctx, vtx.p, wi, nvg.RGB(0, 0, 0), scale=s, length=0.25)
                            draw_arrow(ctx, vtx.p, wo, nvg.RGB(0, 0, 0), scale=s, length=0.25)
                            draw_arrow(ctx, vtx.p, wio, nvg.RGB(0, 128, 0), scale=s, length=0.25)
        elif not show_intermediate_steps:
            pass
            # draw_path_normals(ctx, self.seed_path, scale=s)

        if self.rough_mode:
            pass
        elif self.sms_mode:
            if self.animation_state == 0:
                draw_vertices(ctx, self.seed_points, nvg.RGB(80, 80, 80), s)

            if self.animation_state == 2:
                for seed_path in self.seed_paths:
                    draw_dotted_path_lines(ctx, seed_path, 0.6*s, spacing=0.02)

            if self.animation_state == 1:
                for seed_path in self.seed_paths:
                    draw_path_vertices(ctx, seed_path, '', s)

            elif self.animation_state > 2:
                for solution in self.solution_paths:
                    draw_path_vertices(ctx, solution, '', s)
        elif not show_intermediate_steps:
            pass

            # draw_path_vertices(ctx, self.seed_path, '', s)
            # if self.solution_path:
            #     draw_path_vertices(ctx, self.solution_path, '', s)

        self.knob_start.draw(ctx)
        self.knob_end.draw(ctx)
        if not self.sms_mode:
            if self.solution_path:
                draw_path_vertices(ctx, self.solution_path, '', s)

            self.knob_spec.draw(ctx)

    def layout(self, window):
        strategy_tools = Widget(window)
        strategy_tools.set_layout(BoxLayout(Orientation.Horizontal,
                                            Alignment.Middle, 0, 3))
        Label(strategy_tools, "MNEE vs. SMS:")

        self.strategy_mnee_btn = Button(strategy_tools, "", icons.FA_CIRCLE)
        self.strategy_mnee_btn.set_flags(Button.Flags.RadioButton)
        self.strategy_mnee_btn.set_pushed(self.strategy_type == StrategyType.MNEE)
        def strategy_mnee_cb(state):
            if state:
                self.strategy_type = StrategyType.MNEE
        self.strategy_mnee_btn.set_change_callback(strategy_mnee_cb)

        self.strategy_sms_btn = Button(strategy_tools, "", icons.FA_CERTIFICATE)
        self.strategy_sms_btn.set_flags(Button.Flags.RadioButton)
        self.strategy_sms_btn.set_pushed(self.strategy_type == StrategyType.SMS)
        def strategy_sms_cb(state):
            if state:
                self.strategy_type = StrategyType.SMS
        self.strategy_sms_btn.set_change_callback(strategy_sms_cb)

        Label(strategy_tools, "  N=")
        self.n_bounces_box = IntBox(strategy_tools)
        self.n_bounces_box.set_fixed_size((50, 20))
        self.n_bounces_box.set_value(1)
        self.n_bounces_box.set_default_value("1")
        self.n_bounces_box.set_font_size(20)
        self.n_bounces_box.set_spinnable(True)
        self.n_bounces_box.set_min_value(1)
        self.n_bounces_box.set_value_increment(1)


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

        self.show_constraint_chb = CheckBox(constraint_tools, "Show")
        self.show_constraint_chb.set_checked(False)
        self.flip_constraint_chb = CheckBox(constraint_tools, "Flip")
        self.flip_constraint_chb.set_checked(False)

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

        intermediate_tools = Widget(window)
        intermediate_tools.set_layout(BoxLayout(Orientation.Horizontal,
                                                Alignment.Middle, 0, 3))
        Label(intermediate_tools, "Intermediate steps:")
        self.show_intermediate_steps_chb = CheckBox(intermediate_tools, "")
        self.show_intermediate_steps_chb.set_checked(False)
        Label(intermediate_tools, "Step size:")
        self.step_size_sl = Slider(intermediate_tools)
        self.step_size_sl.set_value(1.0)

        sms_tools = Widget(window)
        sms_tools.set_layout(BoxLayout(Orientation.Horizontal,
                                       Alignment.Middle, 0, 2))
        Label(sms_tools, "Sample")
        self.n_sms_paths_box = IntBox(sms_tools)
        self.n_sms_paths_box.set_fixed_size((50, 20))
        self.n_sms_paths_box.set_value(10)
        self.n_sms_paths_box.set_default_value("10")
        self.n_sms_paths_box.set_font_size(20)
        self.n_sms_paths_box.set_spinnable(True)
        self.n_sms_paths_box.set_min_value(1)
        self.n_sms_paths_box.set_value_increment(1)
        Label(sms_tools, " paths")
        self.sms_btn = Button(sms_tools, "Go", icons.FA_ROCKET)
        self.sms_btn.set_background_color(Color(0, 1.0, 0, 0.1))
        def sms_cb():
            self.sms_mode = not self.sms_mode
            if self.sms_mode:
                self.sms_btn.set_background_color(Color(1.0, 0, 0, 0.1))
                self.rough_btn.set_enabled(False)
            else:
                self.sms_btn.set_background_color(Color(0, 1.0, 0, 0.1))
                self.rough_btn.set_enabled(True)

            if self.sms_mode:
                spec_u_current = self.scene.spec_u_current
                self.seed_paths = []
                self.solution_paths = []

                # N = 1000
                # seed_numbers = np.linspace(0, 1, N)
                # for k in range(N):
                #     self.scene.spec_u_current = seed_numbers[k]

                self.seed_points = []
                N = self.n_sms_paths_box.value()
                for k in range(N):
                    self.scene.spec_u_current = np.random.uniform()

                    it = self.scene.sample_spec_position(self.scene.spec_u_current)
                    self.seed_points.append(it.p)


                    seed_path = self.scene.sample_seed_path(self.n_bounces_box.value())
                    self.seed_paths.append(seed_path.copy())

                    if seed_path.has_specular_segment():
                        solution_path, _ = self.newton_solver(self.scene, seed_path)
                        if solution_path:
                            self.solution_paths.append(solution_path.copy())

                self.scene.spec_u_current = spec_u_current
        self.sms_btn.set_callback(sms_cb)

        rough_tools = Widget(window)
        rough_tools.set_layout(BoxLayout(Orientation.Horizontal,
                                         Alignment.Middle, 0, 2))
        Label(rough_tools, "Sample")
        self.n_normals_box = IntBox(rough_tools)
        self.n_normals_box.set_fixed_size((50, 20))
        self.n_normals_box.set_value(10)
        self.n_normals_box.set_default_value("10")
        self.n_normals_box.set_font_size(20)
        self.n_normals_box.set_spinnable(True)
        self.n_normals_box.set_min_value(1)
        self.n_normals_box.set_value_increment(1)
        Label(rough_tools, " normals ( ")
        self.roughness_box = FloatBox(rough_tools)
        self.roughness_box.set_editable(True)
        self.roughness_box.set_fixed_size((60, 20))
        self.roughness_box.set_value(0.1)
        self.roughness_box.set_default_value("0.1")
        self.roughness_box.set_font_size(20)
        self.roughness_box.set_format("[0-9]*\\.?[0-9]+")
        Label(rough_tools, " )")
        self.rough_btn = Button(rough_tools, "Go", icons.FA_ROCKET)
        self.rough_btn.set_background_color(Color(0, 1.0, 0, 0.1))
        def rough_cb():
            self.rough_mode = not self.rough_mode
            if self.rough_mode:
                self.rough_btn.set_background_color(Color(1.0, 0, 0, 0.1))
                self.sms_btn.set_enabled(False)
            else:
                self.rough_btn.set_background_color(Color(0, 1.0, 0, 0.1))
                self.sms_btn.set_enabled(True)

            if self.rough_mode:
                self.solution_paths = []
                N = self.n_normals_box.value()
                for k in range(N):
                    seed_path = self.seed_path.copy()
                    for k, vtx in enumerate(seed_path):
                        if vtx.shape.type == Shape.Type.Reflection or vtx.shape.type == Shape.Type.Refraction:
                            alpha = self.roughness_box.value()
                            sigma2 = 0.5*alpha*alpha
                            slope = np.random.normal(0, np.sqrt(sigma2))
                            vtx.n_offset = normalize(np.array([-slope, 1]))
                    if seed_path.has_specular_segment():
                        solution_path, _ = self.newton_solver(self.scene, seed_path)
                        if solution_path:
                            self.solution_paths.append(solution_path.copy())
        self.rough_btn.set_callback(rough_cb)

        return [strategy_tools, constraint_tools, steps_eps_tools, sms_tools, rough_tools, intermediate_tools], []

    def keyboard_event(self, key, scancode, action, modifiers):
        super().keyboard_event(key, scancode, action, modifiers)

        if key == glfw.KEY_UP and action == glfw.PRESS:
            self.animation_state += 1
            return True

        if key == glfw.KEY_DOWN and action == glfw.PRESS:
            if self.animation_state > 0:
                self.animation_state -= 1
            return True

        if key == glfw.KEY_RIGHT and action == glfw.PRESS:
            self.animating = not self.animating
            return True

        if key == glfw.KEY_S and action == glfw.PRESS:
            self.sms_mode = not self.sms_mode

            if self.sms_mode:
                spec_u_current = self.scene.spec_u_current
                self.seed_paths = []
                self.solution_paths = []

                # N = 1000
                # seed_numbers = np.linspace(0, 1, N)
                # for k in range(N):
                #     self.scene.spec_u_current = seed_numbers[k]

                self.seed_points = []
                N = self.n_sms_paths_box.value()
                for k in range(N):
                    self.scene.spec_u_current = np.random.uniform()

                    it = self.scene.sample_spec_position(self.scene.spec_u_current)
                    self.seed_points.append(it.p)


                    seed_path = self.scene.sample_seed_path(self.n_bounces_box.value())
                    self.seed_paths.append(seed_path.copy())

                    if seed_path.has_specular_segment():
                        solution_path, _ = self.newton_solver(self.scene, seed_path)
                        if solution_path:
                            self.solution_paths.append(solution_path.copy())

                self.scene.spec_u_current = spec_u_current
                return True

    def max_steps(self):
        value = self.max_steps_sl.value()
        return 1 + int(49*value)

    def eps_threshold(self):
        value = self.eps_sl.value()
        return 10.0**(-(1 + value*7))

    def step_size_scale(self):
        return self.step_size_sl.value()