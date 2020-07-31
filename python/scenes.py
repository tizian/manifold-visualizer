import numpy as np
from scene import Scene
from manifolds import BezierCurve, Circle, ConcaveSegment, ConvexSegment, LinearSegment, Shape
from nanogui import nanovg as nvg
from bezier_shapes import *

def create_scenes():
    scenes = []


    # SIMPLE REFLECTION

    s1 = LinearSegment([0.7, 1.5], [-0.7, 1.5])
    s1.type = Shape.Type.Diffuse
    s1.end = True
    s1.start = True

    s3 = ConvexSegment([-0.6, 0.5], [0.6, 0.5], 2.0, False)
    s3.type = Shape.Type.Reflection
    s3.first_specular = True


    bounds = Circle([0, 0], 100.0)
    bounds.type = Shape.Type.Null
    bounds.visible = False

    scene = Scene([s1, s3, bounds])
    scene.name = "Simple reflection"
    scene.set_start(0.1, -121.65789, 0.9, 0.5)
    scene.offset = [0, -0.75]
    scene.zoom = 0.93
    scenes.append(scene)


    # SIMPLE REFRACTION

    s1 = LinearSegment([-0.7, 0], [0.7, 0])
    s1.type = Shape.Type.Diffuse
    s1.end = True

    s2 = LinearSegment([0.7, 1.5], [-0.7, 1.5])
    s2.type = Shape.Type.Diffuse
    s2.start = True

    s3 = ConvexSegment([-0.6, 0.5], [0.6, 0.5], 2.0, False)
    s3.type = Shape.Type.Refraction
    s3.eta = 1.5
    s3.first_specular = True
    s3.gradient_start = 0.4

    bounds = Circle([0, 0], 100.0)
    bounds.type = Shape.Type.Null
    bounds.visible = False

    scene = Scene([s2, s3, s1, bounds])
    scene.name = "Simple refraction"
    scene.set_start(0.1, -121.429, 0.3429, 0.5)
    scene.offset = [0, -0.75]
    scene.zoom = 0.93
    scenes.append(scene)


    # CONCAVE REFLECTOR

    s1 = LinearSegment([-1, 0], [-0.1, 0])
    s1.type = Shape.Type.Diffuse
    s1.start = True

    s2 = LinearSegment([0.1, 0], [1, 0])
    s2.type = Shape.Type.Diffuse
    s2.end = True

    s3 = ConcaveSegment([0.45, 1], [-0.45, 1], 2.0)
    s3.type = Shape.Type.Reflection
    s3.first_specular = True

    bounds = Circle([0, 0], 100.0)
    bounds.type = Shape.Type.Null
    bounds.visible = False

    scene = Scene([s1, s2, s3, bounds])
    scene.name = "Concave reflector"
    scene.set_start(0.47, 60.54, end_u=0.53, spec_u=-13.34)
    scene.offset = [0, -0.75]
    scene.zoom = 0.93
    scenes.append(scene)


    # REFLECTIVE SPHERE

    s1 = LinearSegment([-1, 0], [-0.1, 0])
    s1.type = Shape.Type.Diffuse
    s1.start = True

    s2 = LinearSegment([0.1, 0], [1, 0])
    s2.type = Shape.Type.Diffuse
    s2.end = True

    s3 = Circle([0.0, 1.5], 0.7)
    s3.type = Shape.Type.Reflection
    s3.first_specular = True

    bounds = Circle([0, 0], 100.0)
    bounds.type = Shape.Type.Null
    bounds.visible = False

    scene = Scene([s1, s2, s3, bounds])
    scene.name = "Reflective sphere"
    scene.set_start(0.43, 52.36, spec_u=0.75)
    scene.offset = [0.13, -0.8]
    scene.zoom = 0.75
    scenes.append(scene)


    # MNEE / REFRACTIVE SPHERE

    s1 = LinearSegment([-1.0, 0], [1.0, 0])
    s1.type = Shape.Type.Diffuse
    s1.end = True

    s2 = Circle([0.0, 0.0], 1.0)
    s2 = ConvexSegment([-0.9, 0], [0.9, 0], 0.9, True)
    s2.type = Shape.Type.Refraction
    s2.eta = 2.0
    s2.first_specular = True

    s3 = LinearSegment([1.15, 1.5], [0.95, 1.8])
    s3.type = Shape.Type.Diffuse
    s3.start = True
    s3.gradient_start = 0.08

    bounds = Circle([0, 0], 100.0)
    bounds.type = Shape.Type.Null
    bounds.visible = False

    scene = Scene([s2, s1, s3, bounds])
    scene.name = "Refractive sphere / MNEE"
    scene.set_start(0.48, -143.97, 0.5, 0.5)
    scene.offset = [0, -1]
    scene.zoom = 0.65
    scenes.append(scene)


    # TWO BOUNCE SPHERE

    s1 = LinearSegment([-0.5, 0], [0.5, 0])
    s1.type = Shape.Type.Diffuse
    s1.start = True

    s2 = Circle([0.0, 1.0], 0.3)
    s2.type = Shape.Type.Refraction
    s2.eta = 1.5
    s2.first_specular = True

    s3 = LinearSegment([0.5, 1.8], [-0.5, 1.8])
    s3.type = Shape.Type.Diffuse
    s3.end = True

    bounds = Circle([0, 0], 100.0)
    bounds.type = Shape.Type.Null
    bounds.visible = False

    scene = Scene([s1, s2, s3, bounds])
    scene.name = "Two-bounce sphere"
    scene.set_start(0.675, 87.7394, 0.7552, 0.5)
    scene.offset = [0, -1]
    scene.zoom = 0.75
    scene.n_bounces_default = 2
    scenes.append(scene)


    # WAVY REFLECTION

    s1 = LinearSegment([-0.7, 0], [0.7, 0])
    s1.type = Shape.Type.Diffuse

    s2 = LinearSegment([0.7, 1.5], [-0.7, 1.5])
    s2.type = Shape.Type.Diffuse
    s2.start = True
    s2.end = True

    plane_x = pts_wavy_plane[0]
    plane_y = pts_wavy_plane[1]
    plane_x *= 0.7;
    plane_y *= 0.7;
    plane_y += 0.08;

    s3 = BezierCurve(list(plane_x.flatten()), list(plane_y.flatten()))
    s3.type = Shape.Type.Reflection
    s3.first_specular = True

    bounds = Circle([0, 0], 100.0)
    bounds.type = Shape.Type.Null
    bounds.visible = False

    scene = Scene([s2, s3, s1, bounds])
    scene.name = "Wavy reflection"
    scene.set_start(0.83, -76.76, 0.2, 0.5)
    scene.offset = [0, -0.75]
    scene.zoom = 0.93
    scenes.append(scene)


    # WAVY REFRACTION / POOL

    s1 = LinearSegment([-0.7, 0], [0.7, 0])
    s1.type = Shape.Type.Diffuse
    s1.end = True

    s2 = LinearSegment([0.7, 1.5], [-0.7, 1.5])
    s2.type = Shape.Type.Diffuse
    s2.start = True

    scale = 0.6
    offset = 0.2
    pool_x = pts_pool[0]
    pool_y = pts_pool[1]
    pool_x *= scale; pool_y *= scale
    pool_y += offset

    s3 = BezierCurve(list(pool_x.flatten()), list(pool_y.flatten()))
    s3.type = Shape.Type.Refraction
    s3.eta = 1.33
    s3.first_specular = True

    s4 = LinearSegment([-0.6, 0.5], [-0.55, 0.5])
    s4.type = Shape.Type.Diffuse
    s4.gradient_start = 9.31
    s4.gradient_width = 0.08
    s4.height = 10.0

    s5 = LinearSegment([0.55, 0.5], [0.6, 0.5])
    s5.type = Shape.Type.Diffuse
    s5.gradient_start = 9.31
    s5.gradient_width = 0.08
    s5.height = 10.0

    bounds = Circle([0, 0], 100.0)
    bounds.type = Shape.Type.Null
    bounds.visible = False

    scene = Scene([s3, s1, s2, s4, s5, bounds])
    scene.name = "Wavy refraction / pool"
    scene.set_start(0.1, -121.429, 0.3849, 0.5)
    scene.offset = [0, -0.75]
    scene.zoom = 0.93
    scenes.append(scene)


    # SPHERE (MANY BOUNCES)

    s1 = LinearSegment([-0.8, 0], [0.8, 0])
    s1.type = Shape.Type.Diffuse
    s1.start = True
    s1.end = True

    s2 = Circle([0.0, 1.0], 0.5)
    s2.type = Shape.Type.Refraction
    s2.eta = 1.5
    s2.first_specular = True

    s3 = LinearSegment([0.8, 2], [-0.8, 2])
    s3.type = Shape.Type.Reflection

    bounds = Circle([0, 0], 100.0)
    bounds.type = Shape.Type.Null
    bounds.visible = False

    scene = Scene([s1, s2, s3, bounds])
    scene.name = "Sphere (many bounces)"
    scene.set_start(0.41, 100.61, spec_u=0.6956925392150879)
    scene.offset = [0, -1]
    scene.zoom = 0.75
    scene.n_bounces_default = 5
    scenes.append(scene)


    # BUNNY

    s1 = LinearSegment([-0.8, 0], [0.8, 0])
    s1.type = Shape.Type.Diffuse
    s1.start = True
    s1.end = True

    bunny_x = pts_bunny[0]; bunny_x *= 0.6
    bunny_y = pts_bunny[1]; bunny_y *= 0.6; bunny_y += 1.0
    s2 = BezierCurve(list(bunny_x.flatten()), list(bunny_y.flatten()))
    s2.type = Shape.Type.Refraction
    s2.eta = 1.5
    s2.first_specular = True

    s3 = LinearSegment([0.8, 2], [-0.8, 2])
    s3.type = Shape.Type.Reflection

    bounds = Circle([0, 0], 100.0)
    bounds.type = Shape.Type.Null
    bounds.visible = False

    scene = Scene([s1, s2, s3, bounds])
    scene.name = "Bunny"
    scene.set_start(0.644, 85.17827, end_u=0.39, spec_u=0.4038328230381012)
    scene.offset = [0, -1]
    scene.zoom = 0.75
    scene.n_bounces_default = 7
    scenes.append(scene)


    # DRAGON

    s1 = LinearSegment([-0.7, 0], [0.7, 0])
    s1.type = Shape.Type.Diffuse

    s2 = LinearSegment([0.7, 1.5], [-0.7, 1.5])
    s2.type = Shape.Type.Diffuse
    s2.start = True
    s2.end = True

    dragon_x = pts_dragon[0]
    dragon_y = pts_dragon[1]
    dragon_hole_x = pts_dragon_hole[0]
    dragon_hole_y = pts_dragon_hole[1]
    dragon_x *= 0.7; dragon_hole_x *= 0.7
    dragon_y *= 0.7; dragon_hole_y *= 0.7
    dragon_y += 0.48; dragon_hole_y += 0.48


    s3 = BezierCurve(list(dragon_x.flatten()), list(dragon_y.flatten()))
    s3.type = Shape.Type.Reflection
    s3.first_specular = True
    s3.name = "dragon"

    s_hole = BezierCurve(list(dragon_hole_x.flatten()), list(dragon_hole_y.flatten()))
    s_hole.type = Shape.Type.Reflection
    # s_hole.flip()
    s_hole.hole = True
    s_hole.parent = "dragon"

    bounds = Circle([0, 0], 100.0)
    bounds.type = Shape.Type.Null
    bounds.visible = False

    scene = Scene([s2, s3, s1, s_hole, bounds])
    scene.name = "Dragon"
    scene.set_start(0.104, -135.0, 0.832, 0.5)
    scene.offset = [0, -0.75]
    scene.zoom = 0.93
    scenes.append(scene)


    # SIGGRAPH LOGO

    s1 = LinearSegment([-0.7, 0], [0.7, 0])
    s1.type = Shape.Type.Diffuse
    s1.end = True

    s2 = LinearSegment([0.7, 1.5], [-0.7, 1.5])
    s2.type = Shape.Type.Diffuse
    s2.start = True

    siggraph_1_x = pts_siggraph_1[0]
    siggraph_1_y = pts_siggraph_1[1]
    siggraph_2_x = pts_siggraph_2[0]
    siggraph_2_y = pts_siggraph_2[1]
    siggraph_3_x = pts_siggraph_3[0]
    siggraph_3_y = pts_siggraph_3[1]
    siggraph_4_x = pts_siggraph_4[0]
    siggraph_4_y = pts_siggraph_4[1]
    mitsuba_x = pts_mitsuba[0]
    mitsuba_y = pts_mitsuba[1]

    scale = 0.65
    offset = 0.7
    siggraph_1_x *= scale; siggraph_2_x *= scale; siggraph_3_x *= scale; siggraph_4_x *= scale;
    siggraph_1_y *= scale; siggraph_2_y *= scale; siggraph_3_y *= scale; siggraph_4_y *= scale;
    siggraph_1_y += offset; siggraph_2_y += offset; siggraph_3_y += offset; siggraph_4_y += offset;
    mitsuba_x *= scale; mitsuba_y *= scale
    mitsuba_y += offset

    s3 = BezierCurve(list(siggraph_1_x.flatten()), list(siggraph_1_y.flatten()))
    s3.type = Shape.Type.Refraction
    s3.eta = 1.5
    s3.first_specular = True

    s4 = BezierCurve(list(siggraph_2_x.flatten()), list(siggraph_2_y.flatten()))
    s4.type = Shape.Type.Refraction
    s4.eta = 1.5

    s5 = BezierCurve(list(siggraph_3_x.flatten()), list(siggraph_3_y.flatten()))
    s5.type = Shape.Type.Refraction
    s5.eta = 1.5

    s6 = BezierCurve(list(siggraph_4_x.flatten()), list(siggraph_4_y.flatten()))
    s6.type = Shape.Type.Refraction
    s6.eta = 1.5

    s7 = BezierCurve(list(mitsuba_x.flatten()), list(mitsuba_y.flatten()))
    s7.type = Shape.Type.Refraction
    s7.eta = 1.5

    bounds = Circle([0, 0], 100.0)
    bounds.type = Shape.Type.Null
    bounds.visible = False

    scene = Scene([s1, s2, s3, s4, s5, bounds])
    scene.name = "SIGGRAPH logo"
    scene.set_start(0.38, -85.24, 0.57, 0.89)
    scene.offset = [0, -0.75]
    scene.zoom = 0.93
    scene.n_bounces_default = 6
    scenes.append(scene)


    # MITSUBA LOGO

    s1 = LinearSegment([-0.7, 0], [0.7, 0])
    s1.type = Shape.Type.Diffuse

    s2 = LinearSegment([0.7, 1.5], [-0.7, 1.5])
    s2.type = Shape.Type.Diffuse
    s2.start = True
    s2.end = True

    mitsuba_x = pts_mitsuba[0]
    mitsuba_y = pts_mitsuba[1]
    mitsuba_x *= 0.7
    mitsuba_y *= 0.7

    s3 = BezierCurve(list(mitsuba_x.flatten()), list(mitsuba_y.flatten()))
    s3.type = Shape.Type.Reflection
    s3.first_specular = True

    bounds = Circle([0, 0], 100.0)
    bounds.type = Shape.Type.Null
    bounds.visible = False

    scene = Scene([s2, s3, s1, s_hole, bounds])
    scene.name = "Mitsuba logo"
    scene.set_start(0.347, -109.09, 0.832, 0.5)
    scene.offset = [0, -0.75]
    scene.zoom = 0.93
    scenes.append(scene)


    # TEAPOT

    s1 = LinearSegment([-0.7, 0], [0.7, 0])
    s1.type = Shape.Type.Diffuse
    s1.end = True

    s2 = LinearSegment([0.7, 1.5], [-0.7, 1.5])
    s2.type = Shape.Type.Diffuse
    s2.start = True

    teapot_x = pts_teapot[0]
    teapot_y = pts_teapot[1]
    teapot_hole_x = pts_teapot_hole[0]
    teapot_hole_y = pts_teapot_hole[1]
    teapot_x *= 0.8; teapot_hole_x *= 0.8
    teapot_y *= 0.8; teapot_hole_y *= 0.8
    teapot_y += 0.6; teapot_hole_y += 0.6

    s3 = BezierCurve(list(teapot_x.flatten()), list(teapot_y.flatten()))
    s3.type = Shape.Type.Refraction
    s3.first_specular = True
    s3.eta = 1.5
    s3.name = "teapot"

    s_hole = BezierCurve(list(teapot_hole_x.flatten()), list(teapot_hole_y.flatten()))
    s_hole.type = Shape.Type.Refraction
    # s_hole.flip()
    s_hole.hole = True
    s_hole.eta = 1.5
    s_hole.parent = "teapot"

    bounds = Circle([0, 0], 100.0)
    bounds.type = Shape.Type.Null
    bounds.visible = False

    scene = Scene([s2, s3, s1, s_hole, bounds])
    scene.name = "Teapot"
    scene.set_start(0.716, -69.54, end_u=0.55298, spec_u=0.22485)
    scene.offset = [0, -0.75]
    scene.zoom = 0.93
    scene.n_bounces_default = 2
    scenes.append(scene)


    return scenes
