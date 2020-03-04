import numpy as np
from nanogui import nanovg as nvg
from misc import *
import copy

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

def draw_path_lines(ctx, path, modifier='', scale=1):
    if modifier == 'tangent' or modifier == 'seed':
        ctx.StrokeColor(nvg.RGB(255, 0, 0))
        ctx.StrokeWidth(0.004*scale)
    elif modifier == 'manifold':
        ctx.StrokeColor(nvg.RGB(114, 104, 130))
        ctx.StrokeWidth(0.008*scale)
    elif modifier == '':
        ctx.StrokeColor(nvg.RGB(80, 80, 80))
        ctx.StrokeWidth(0.008*scale)
    for i in range(len(path) - 1):
        v0 = path[i].p
        v1 = path[i+1].p

        ctx.BeginPath()
        ctx.MoveTo(v0[0], v0[1])
        ctx.LineTo(v1[0], v1[1])
        ctx.Stroke()

def draw_intermediate_path_lines(ctx, path, color, scale=1):
    ctx.StrokeColor(color)
    ctx.StrokeWidth(0.004*scale)
    for i in range(len(path) - 1):
        v0 = path[i].p
        v1 = path[i+1].p

        ctx.BeginPath()
        ctx.MoveTo(v0[0], v0[1])
        ctx.LineTo(v1[0], v1[1])
        ctx.Stroke()

def draw_dotted_path_lines(ctx, path, scale=1.0, spacing=0.05):
    color = nvg.RGB(80, 80, 80)
    for i in range(len(path) - 1):
        v0 = path[i].p
        v1 = path[i+1].p
        draw_dotted_line(ctx, v0, v1, color, scale=scale, spacing=spacing)

def draw_path_vertices(ctx, path, modifier='', scale=1):
    if modifier == 'seed':
        ctx.FillColor(nvg.RGB(255, 0, 0))
    elif modifier == 'manifold':
        ctx.FillColor(nvg.RGB(114, 104, 130))
    else:
        ctx.FillColor(nvg.RGB(80, 80, 80))

    ctx.StrokeColor(nvg.RGB(255, 255, 255))
    ctx.StrokeWidth(0.005*scale)
    for i in range(0, len(path)):
        vtx = path[i]
        ctx.BeginPath()
        ctx.Circle(vtx.p[0], vtx.p[1], 0.015*scale)
        ctx.Fill()
        if modifier != 'seed':
            ctx.Stroke()

def draw_points(ctx, positions, color, scale=1):
    ctx.Save()
    ctx.FillColor(color)
    for p in positions:
        ctx.BeginPath()
        ctx.Circle(p[0], p[1], 0.008*scale)
        ctx.Fill()
    ctx.Restore()

def draw_vertices(ctx, positions, color, scale=1):
    ctx.Save()
    ctx.FillColor(color)

    ctx.StrokeColor(nvg.RGB(255, 255, 255))
    ctx.StrokeWidth(0.005*scale)
    for p in positions:
        ctx.BeginPath()
        ctx.Circle(p[0], p[1], 0.015*scale)
        ctx.Fill()
        ctx.Stroke()
    ctx.Restore()

def draw_line(ctx, a, b, color, scale=1.0, endcap_a=False, endcap_b=False):
    ctx.Save()
    ctx.StrokeWidth(0.01*scale)
    ctx.StrokeColor(color)

    ctx.BeginPath()
    ctx.MoveTo(a[0], a[1])
    ctx.LineTo(b[0], b[1])
    ctx.Stroke()

    ctx.StrokeWidth(0.005*scale)
    v = normalize(b - a)
    v_p = np.array([-v[1], v[0]])

    if endcap_a:
        ctx.BeginPath()
        a1 = a + 0.02*v_p
        a2 = a - 0.02*v_p
        ctx.MoveTo(a1[0], a1[1])
        ctx.LineTo(a2[0], a2[1])
        ctx.Stroke()

    if endcap_b:
        ctx.BeginPath()
        b1 = b + 0.02*v_p
        b2 = b - 0.02*v_p
        ctx.MoveTo(b1[0], b1[1])
        ctx.LineTo(b2[0], b2[1])
        ctx.Stroke()

    ctx.Restore()

def draw_dotted_line(ctx, a, b, color, scale=1.0, spacing=0.05):
    ctx.Save()
    ctx.FillColor(color)

    ctx.BeginPath()
    v = b - a
    dist = norm(v)
    v /= dist
    k = 0
    while True:
        offset = (k+0.5)*spacing*v
        if norm(offset) > dist:
            break
        c = a + offset
        ctx.Circle(c[0], c[1], 0.005*scale)
        k += 1
    ctx.Fill()
    ctx.Restore()

def draw_angle(ctx, p, r, phi_0, phi_1, color, scale=1.0, flip=False):
    o = nvg.NVGwinding.CCW if flip else nvg.NVGwinding.CW
    ctx.Save()
    ctx.StrokeWidth(0.01*scale)
    ctx.StrokeColor(color)
    ctx.BeginPath()
    ctx.Arc(p[0], p[1], r, phi_0, phi_1, o)
    ctx.Stroke()
    ctx.Restore()

def draw_arrow_helper(ctx, p0, v, scale=1.0, length=0.12, head_scale=1.0):
    theta = np.arctan2(v[1], v[0])
    p1 = p0 + v * length * scale

    ctx.Save()
    ctx.StrokeWidth(0.01*scale)

    ctx.BeginPath()
    ctx.MoveTo(p0[0], p0[1])
    ctx.LineTo(p1[0], p1[1])
    ctx.Stroke()

    ctx.Restore()

    v_p = np.array([-v[1], v[0]])
    p_a = p1 - 0.02*head_scale*scale*v_p - 0.01*head_scale*scale*v
    p_b = p1 + 0.02*head_scale*scale*v_p - 0.01*head_scale*scale*v

    p_tip = p1 + v * 0.03*head_scale * scale

    ctx.BeginPath()
    ctx.MoveTo(p_tip[0], p_tip[1])
    ctx.LineTo(p_a[0], p_a[1])
    ctx.ArcTo(p1[0], p1[1], p_b[0], p_b[1], scale*0.028)
    ctx.LineTo(p_b[0], p_b[1])
    ctx.LineTo(p_tip[0], p_tip[1])
    ctx.Fill()

def draw_arrow(ctx, p, v, color, scale=1.0, length=1.0, head_scale=1.0):
    ctx.Save()
    ctx.FillColor(color)
    ctx.StrokeColor(color)
    draw_arrow_helper(ctx, p, v, scale, length, head_scale)
    ctx.Restore()

def draw_path_normals(ctx, path, scale=1.0):
    ctx.Save()
    ctx.StrokeWidth(0.01*scale)
    ctx.FillColor(nvg.RGB(255, 0, 0))
    ctx.StrokeColor(nvg.RGB(255, 0, 0))
    for i in range(1, len(path)-1):
        vtx = path[i]
        draw_arrow_helper(ctx, vtx.p, vtx.n, scale)
    ctx.Restore()

def draw_path_tangents(ctx, path, scale=1.0):
    ctx.Save()
    ctx.FillColor(nvg.RGB(0, 0, 255))
    ctx.StrokeColor(nvg.RGB(0, 0, 255))
    ctx.StrokeWidth(0.01*scale)
    for i in range(1, len(path)-1):
        vtx = path[i]
        draw_arrow_helper(ctx, vtx.p, vtx.s, scale)
    ctx.Restore()

def draw_path_origin(ctx, path, last_picked_vtx_idx):
    if last_picked_vtx_idx == None:
        return

    ctx.FillColor(nvg.RGB(255, 255, 255))
    ctx.StrokeColor(nvg.RGB(255, 255, 255))
    ctx.StrokeWidth(0.01)

    i0 = -1 if last_picked_vtx_idx == 0 else 0
    i1 = -2 if last_picked_vtx_idx == 0 else 1
    p0 = copy.copy(path[i0].p)
    p1 = copy.copy(path[i1].p)
    wi = p1 - p0
    theta = np.arctan2(wi[1], wi[0])
    wi = np.array([np.cos(theta), np.sin(theta)])
    p1 = p0 + wi * 0.08

    ctx.BeginPath()
    ctx.MoveTo(p0[0], p0[1])
    ctx.LineTo(p1[0], p1[1])
    ctx.Stroke()

    wi2 = np.array([np.cos(theta+0.3), np.sin(theta+0.3)])
    wi3 = np.array([np.cos(theta-0.3), np.sin(theta-0.3)])
    p2 = p0 + wi2 * 0.08
    p3 = p0 + wi3 * 0.08
    p4 = p1 + wi  * 0.03

    ctx.BeginPath()
    ctx.MoveTo(p4[0], p4[1])
    ctx.LineTo(p2[0], p2[1])
    ctx.LineTo(p3[0], p3[1])
    ctx.LineTo(p4[0], p4[1])
    ctx.Fill()
