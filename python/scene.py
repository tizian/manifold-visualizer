import numpy as np
import manifolds
from manifolds import Scene as CppScene
from manifolds import Ray2f, Shape
from misc import *
from path import Path
from draw import *

class Scene:
    def __init__(self, shapes):
        self.shapes = shapes
        self.offset = [0, 0]
        self.zoom   = 1.0
        self.scale  = 1.0

        self.start_u_default = 0
        self.start_u_current = 0
        self.start_angle_default = 0
        self.start_angle_current = 0
        self.end_u_default = 0
        self.end_u_current = 0
        self.spec_u_default = 0
        self.spec_u_current = 0
        self.n_bounces_default = 1

        self.cpp_scene = CppScene()

        shape_id = 0
        for s in shapes:
            s.id = shape_id
            self.cpp_scene.add_shape(s)
            shape_id += 1

    def set_start(self, start_u, start_angle, end_u=0.5, spec_u=0.5):
        self.start_u_default = start_u
        self.start_angle_default = start_angle
        self.end_u_default = end_u
        self.spec_u_default = spec_u

        self.start_u_current = start_u
        self.start_angle_current = start_angle
        self.end_u_current = end_u
        self.spec_u_current = spec_u

    def start_shape(self):
        return self.cpp_scene.start_shape()

    def end_shape(self):
        return self.cpp_scene.end_shape()

    def first_specular_shape(self):
        return self.cpp_scene.first_specular_shape()

    def draw(self, ctx):
        for shape in self.shapes:
            if shape.type == Shape.Type.Emitter:
                for t in np.linspace(0, 1, 10):
                    it = shape.sample_position(t)
                    draw_arrow(ctx, it.p, it.n, nvg.RGB(255, 255, 180), scale=0.5, length=0.03)

        self.cpp_scene.draw(ctx)

    def ray_intersect(self, ray):
        # Trace ray against C++ representation
        it = self.cpp_scene.ray_intersect(ray)

        if it.is_valid():
            # We now need to track the relative IOR change at this interaction
            wi = -ray.d
            it.eta = it.shape.eta
            it.n_offset = np.array([0, 1])

        return it

    def sample_start_position(self, u):
        it = self.cpp_scene.start_shape().sample_position(u)
        it.eta = it.shape.eta
        it.n_offset = np.array([0, 1])
        return it

    def sample_end_position(self, u):
        it = self.cpp_scene.end_shape().sample_position(u)
        it.eta = it.shape.eta
        it.n_offset = np.array([0, 1])
        return it

    def sample_spec_position(self, u):
        it = self.cpp_scene.first_specular_shape().sample_position(u)
        it.eta = it.shape.eta
        it.n_offset = np.array([0, 1])
        return it

    def sample_path(self):
        it = self.sample_start_position(self.start_u_current)

        path = Path()
        path.append(it)

        theta = np.radians(self.start_angle_current)
        wo = [np.cos(theta), np.sin(theta)]
        if wo @ it.n < 0.0:
            return path

        while True:
            ray = Ray2f(it.p, wo)

            it = self.ray_intersect(ray)
            wi = -ray.d

            path.append(it)

            m = it.s * it.n_offset[0] + it.n * it.n_offset[1]
            if it.shape.type == Shape.Type.Reflection:
                if wi @ it.n < 0:
                    break
                wo = reflect(wi, m)
            elif it.shape.type == Shape.Type.Refraction:
                wo = refract(wi, m, it.shape.eta)
            else:
                break

            if not wo[0]:
                break
            wo = wo[1]

        return path

    def sample_seed_path(self, n_spec_bounces=1):
        path = Path()

        it1 = self.sample_start_position(self.start_u_current)
        it2 = self.sample_spec_position(self.spec_u_current)
        wo = normalize(it2.p - it1.p)
        if wo @ it1.n < 0.0:
            return path

        ray = Ray2f(it1.p, wo)
        it = self.ray_intersect(ray)
        if not it.is_valid() or (it.shape != it2.shape):
            return path
        it2 = it

        path.append(it1)
        path.append(it)

        while True:
            wi = -wo
            if len(path) - 1 >= n_spec_bounces:
                break

            m = it.s * it.n_offset[0] + it.n * it.n_offset[1]
            if it.shape.type == Shape.Type.Reflection:
                if wi @ it.n < 0:
                    break
                wo = reflect(wi, m)
            elif it.shape.type == Shape.Type.Refraction:
                wo = refract(wi, m, it.shape.eta)
            else:
                print("Should not happen!!")
                break

            if not wo[0]:
                break
            wo = wo[1]

            ray = Ray2f(it.p, wo)
            it = self.ray_intersect(ray)
            if not (it.shape.type == Shape.Type.Reflection or it.shape.type == Shape.Type.Refraction):
                break

            path.append(it)

        it3 = self.sample_end_position(self.end_u_current)
        path.append(it3)

        if len(path) != n_spec_bounces + 2:
            return Path()

        return path

    def sample_mnee_seed_path(self):
        path = Path()

        it1 = self.sample_start_position(self.start_u_current)
        it3 = self.sample_end_position(self.end_u_current)

        wo = normalize(it3.p - it1.p)
        if wo @ it1.n < 0.0:
            return path
        path.append(it1)

        it = it1
        while True:
            ray = Ray2f(it.p, wo)

            it = self.ray_intersect(ray)

            if it.shape.type == Shape.Type.Reflection:
                break
            elif it.shape.type == Shape.Type.Refraction:
                pass
            else:
                break

            path.append(it)

        it3 = self.sample_end_position(self.end_u_current)
        path.append(it3)

        return path

    def reproject_path_me(self, offset_vertices):
        path = Path()

        p0 = offset_vertices[0]
        t0 = self.cpp_scene.start_shape().project(p0)
        it = self.cpp_scene.start_shape().sample_position(t0)
        path.append(it)

        p1 = offset_vertices[1]
        wo = normalize(p1 - p0)

        while True:
            ray = Ray2f(it.p, wo)

            it = self.ray_intersect(ray)
            wi = -ray.d

            path.append(it)

            m = it.s * it.n_offset[0] + it.n * it.n_offset[1]
            if it.shape.type == Shape.Type.Reflection:
                if wi @ it.n < 0:
                    break
                wo = reflect(wi, m)
            elif it.shape.type == Shape.Type.Refraction:
                wo = refract(wi, m, it.shape.eta)
            else:
                break

            if not wo[0]:
                break
            wo = wo[1]

        return path

    def reproject_path_sms(self, offset_vertices, previous_path, n_spec_bounces=1):
        path = Path()

        p1 = offset_vertices[0]
        t1 = self.cpp_scene.start_shape().project(p1)
        it1 = self.cpp_scene.start_shape().sample_position(t1)

        p2 = offset_vertices[1]
        wo = normalize(p2 - p1)
        if wo @ it1.n < 0.0:
            return path

        ray = Ray2f(p1, wo)
        it2 = self.ray_intersect(ray)
        if it2.shape.id != self.cpp_scene.first_specular_shape().id:
            return path
        it2.n_offset = previous_path.vertices[1].n_offset

        path.append(it1)
        path.append(it2)

        it = it2
        while True:
            wi = -wo
            if len(path) - 1 >= n_spec_bounces:
                break

            m = it.s * it.n_offset[0] + it.n * it.n_offset[1]
            if it.shape.type == Shape.Type.Reflection:
                if wi @ it.n < 0:
                    break
                wo = reflect(wi, m)
            elif it.shape.type == Shape.Type.Refraction:
                wo = refract(wi, m, it.shape.eta)
            else:
                print("Should not happen!!")
                break

            if not wo[0]:
                break
            wo = wo[1]

            ray = Ray2f(it.p, wo)
            it = self.ray_intersect(ray)
            if not (it.shape.type == Shape.Type.Reflection or it.shape.type == Shape.Type.Refraction):
                break
            if len(path) > len(previous_path):
                break

            it.n_offset = previous_path.vertices[len(path)].n_offset
            path.append(it)

        it3 = self.sample_end_position(self.end_u_current)
        path.append(it3)

        if len(path) != n_spec_bounces + 2:
            return Path()

        return path