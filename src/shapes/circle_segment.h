#pragma once

#include <shape.h>
#include <nanovg.h>

class CircleSegment : public Shape {
public:
    CircleSegment(const Point2f &a, const Point2f &b, float arc_radius)
        : Shape(), m_a(a), m_b(b), m_arc_radius(arc_radius) {
            Vector2f dir = m_b - m_a;
            float length = norm(dir);
            Vector2f n(-dir[1], dir[0]);
            n *= rcp(length);
            float phi = atan2(n.y(), n.x());
            float d_phi = asin(0.5f*length*rcp(m_arc_radius));
            m_phi_0 = phi + d_phi;
            m_phi_1 = phi - d_phi;

            float offset = safe_sqrt(sqr(m_arc_radius) - sqr(0.5f*length));
            m_center = 0.5f*(m_a + m_b) - n*offset;
        }

    Interaction sample_position(float sample) const override {
        float phi = lerp(sample, m_phi_0, m_phi_1);
        auto [sp, cp] = sincos(phi);
        Point2f p_local(cp, sp);

        Interaction in;
        in.p = m_center + m_arc_radius*p_local;
        in.n = p_local;
        in.s = Vector2f(-in.n[1], in.n[0]);
        in.dp_du = 2.f*Pi*Vector2f(-p_local[1], p_local[0]);
        float inv_radius = rcp(m_arc_radius);
        in.dn_du = in.dp_du*inv_radius;
        in.u = sample;
        in.shape = this;
        return in;
    }

    float project(const Point2f &p) const override {
        // Vector2f v = m_b - m_a;
        // float scale = rcp(dot(v, v));

        // float t = dot((p - m_a), v)*scale;
        // return min(1.f, max(0.f, t));
    }

    std::pair<bool, float> ray_intersect(const Ray2f &ray) const override {
        // float mint = ray.mint,
        //       maxt = ray.maxt;

        // Vector2f v1 = ray.o - m_a,
        //          v2 = m_b - m_a;
        // Vector2f v3;
        // if (cross(v1, v2) > 0) {
        //     v3 = Vector2f(ray.d[1], -ray.d[0]);
        // } else {
        //     v3 = Vector2f(-ray.d[1], ray.d[0]);
        // }

        // float denom = dot(v2, v3);
        // if (denom == 0)
        //     return { false, Infinity };

        // float t1 = abs(cross(v2, v1)) / denom,
        //       t2 = dot(v1, v3) / denom;

        // if (t1 < mint || t1 > maxt || t2 < Epsilon || t2 > (1.f + Epsilon))
        //     return { false, Infinity };
        // return { true, t1 };
    }

    Interaction fill_interaction(const Ray2f &ray) const override {
        // Interaction in;
        // in.p = ray(in.rayt);
        // in.s = normalize(m_b - m_a);
        // in.n = Vector2f(-in.s[1], in.s[0]);
        // in.dp_du = m_b - m_a;
        // in.dn_du = Vector2f(0, 0);
        // in.u = project(in.p);
        // return in;
    }

    void flip() override {
        std::swap(m_a, m_b);
    }

    void draw(NVGcontext *ctx, bool hole=false) const override {
        if (hole) return;

        Shape::draw(ctx);
        nvgSave(ctx);

        NVGcolor fill_color;
        if (type == Type::Reflection) {
            fill_color = nvgRGB(235, 200, 91);
        } else if (type == Type::Refraction) {
            fill_color = nvgRGBA(128, 200, 255, 128);
        } else {
            fill_color = nvgRGB(180, 180, 180);
        }
        NVGcolor transparent = nvgRGBA(0, 0, 0, 0);

        // The rounded rectangles and gradients behave inconsistently
        // when elements get too small in nanovg, so we work in a scaled coord.
        // system here.
        float nvg_scale     = 1e2f,
              inv_nvg_scale = rcp(nvg_scale);
        nvgScale(ctx, inv_nvg_scale, inv_nvg_scale);

        auto nvgLinearGradientS = [&](NVGcontext *ctx, float sx, float sy, float ex, float ey,
                                      NVGcolor icolor, NVGcolor ecolor) {
            return nvgLinearGradient(ctx, nvg_scale*sx, nvg_scale*sy, nvg_scale*ex, nvg_scale*ey,
                                     icolor, ecolor);
        };
        auto nvgMoveToS = [&](NVGcontext *ctx, float x, float y) {
            nvgMoveTo(ctx, nvg_scale*x, nvg_scale*y);
        };
        auto nvgLineToS = [&](NVGcontext *ctx, float x, float y) {
            nvgLineTo(ctx, nvg_scale*x, nvg_scale*y);
        };
        auto nvgArcS = [&](NVGcontext *ctx, float cx, float cy, float r, float a0, float a1, int dir) {
            nvgArc(ctx, nvg_scale*cx, nvg_scale*cy, nvg_scale*r, a0, a1, dir);
        };

        // Another limitation of nanovg is that rectangles are always axis-aligned.
        // We need to do some more coordinate transforms to generalize.
        float phi = atan2(m_b[1] - m_a[1], m_b[0] - m_a[0]);
        auto [sp, cp] = sincos(phi);
        float length = norm(m_b - m_a);

        Matrix2f R  = Matrix2f(cp, -sp, sp, cp),
                 Ri = transpose(R),
                 Si = Matrix2f(rcp(length));

        Point2f ap = Si * Ri * m_a,
                bp = Si * Ri * m_b;
        float arc_radius = rcp(length) * m_arc_radius;

        nvgStrokeWidth(ctx, nvg_scale*0.005f*rcp(length));
        nvgRotate(ctx, phi);
        nvgScale(ctx, length, length);

        // Set up gradients
        Point2f p0 = 0.5f*(ap + bp),
                p1 = p0 - Vector2f(0.f, gradient_start),
                p2 = p1 - Vector2f(0.f, gradient_width);
        auto fill_grad   = nvgLinearGradientS(ctx, p1[0], p1[1], p2[0], p2[1],
                                              fill_color, transparent);
        auto stroke_grad = nvgLinearGradientS(ctx, p1[0], p1[1], p2[0], p2[1],
                                              nvgRGBA(0, 0, 0, 255), transparent);
        nvgFillPaint(ctx, fill_grad);
        nvgStrokePaint(ctx, stroke_grad);

        nvgBeginPath(ctx);

        // Main arc
        float offset = safe_sqrt(sqr(arc_radius) - 0.25f);
        Point2f c_main = Point2f(ap[0] + 0.5f, bp[1] - offset);
        float alpha = asin(0.5f*rcp(arc_radius));

        // Smaller arcs left and right to transition smoothly to vertical
        Vector2f n_left = normalize(ap - c_main),
                 n_right = normalize(bp - c_main);
        Point2f c_left = ap - corner_radius*n_left,
                c_right = bp - corner_radius*n_right;
        float beta_left = atan2(n_left.y(), n_left.x()),
              beta_right = atan2(n_right.y(), n_right.x());
        if (beta_left < 0.f) beta_left += 2.f*Pi;
        if (beta_right < 0.f) beta_right += 2.f*Pi;

        if (abs(beta_right) > Epsilon)
            nvgArcS(ctx, c_right[0], c_right[1], corner_radius, 0.f, beta_right, NVG_CW);
        nvgArcS(ctx, c_main[0], c_main[1], arc_radius, 0.5f*Pi - alpha, 0.5f*Pi + alpha, NVG_CW);
        if (abs(beta_left - Pi) > Epsilon)
            nvgArcS(ctx, c_left[0], c_left[1], corner_radius, beta_left, Pi, NVG_CW);

        // Rest of shape
        Point2f d_left = c_left - Vector2f(corner_radius, 0.f),
                e_left = d_left - Vector2f(0.f, 1.f),
                d_right = c_right + Vector2f(corner_radius, 0.f),
                e_right = d_right - Vector2f(0.f, 1.f);

        nvgMoveToS(ctx, d_left[0], d_left[1]);
        nvgLineToS(ctx, e_left[0], e_left[1]);
        nvgLineToS(ctx, e_right[0], e_right[1]);
        nvgLineToS(ctx, d_right[0], d_right[1]);

        nvgFill(ctx);
        nvgStroke(ctx);

        nvgRestore(ctx);

        // nvgBeginPath(ctx);
        // nvgStrokeColor(ctx, nvgRGB(255, 0, 0));
        // nvgMoveTo(ctx, m_a[0], m_a[1]);
        // nvgLineTo(ctx, m_b[0], m_b[1]);
        // nvgStroke(ctx);
    }

    std::string to_string() const override {
        std::ostringstream oss;
        oss << "CircleSegment[" << std::endl
            << "  a = " << m_a << "," << std::endl
            << "  b = " << m_b << std::endl
            << "]";
        return oss.str();
    }

protected:
    Point2f m_a, m_b;
    float m_arc_radius;
    Point2f m_center;
    float m_phi_0, m_phi_1;

public:
    float gradient_start = 0.01f,
          gradient_width = 0.03f;
    float corner_radius = 0.02f;
};
