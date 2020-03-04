#pragma once

#include <shape.h>
#include <nanovg.h>

class LinearSegment : public Shape {
public:
    LinearSegment(const Point2f &a, const Point2f &b)
        : Shape(), m_a(a), m_b(b) { }

    Interaction sample_position(float sample) const override {
        Interaction in;
        in.p = m_a + (m_b - m_a)*sample;
        in.s = normalize(m_b - m_a);
        in.n = Vector2f(-in.s[1], in.s[0]);
        in.dp_du = m_b - m_a;
        in.dn_du = Vector2f(0, 0);
        in.shape = this;
        in.u = sample;
        return in;
    }

    float project(const Point2f &p) const override {
        Vector2f v = m_b - m_a;
        float scale = rcp(dot(v, v));

        float t = dot((p - m_a), v)*scale;
        return min(1.f, max(0.f, t));
    }

    std::pair<bool, float> ray_intersect(const Ray2f &ray) const override {
        float mint = ray.mint,
              maxt = ray.maxt;

        Vector2f v1 = ray.o - m_a,
                 v2 = m_b - m_a;
        Vector2f v3;
        if (cross(v1, v2) > 0) {
            v3 = Vector2f(ray.d[1], -ray.d[0]);
        } else {
            v3 = Vector2f(-ray.d[1], ray.d[0]);
        }

        float denom = dot(v2, v3);
        if (denom == 0)
            return { false, Infinity };

        float t1 = abs(cross(v2, v1)) / denom,
              t2 = dot(v1, v3) / denom;

        if (t1 < mint || t1 > maxt || t2 < Epsilon || t2 > (1.f + Epsilon))
            return { false, Infinity };
        return { true, t1 };
    }

    Interaction fill_interaction(const Ray2f &ray) const override {
        Interaction in;
        in.p = ray(in.rayt);
        in.s = normalize(m_b - m_a);
        in.n = Vector2f(-in.s[1], in.s[0]);
        in.dp_du = m_b - m_a;
        in.dn_du = Vector2f(0, 0);
        in.u = project(in.p);
        return in;
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

        auto nvgRectS = [&](NVGcontext *ctx, float x, float y, float w, float h, float r) {
            nvgRoundedRectVarying(ctx, nvg_scale*x, nvg_scale*y, nvg_scale*w, nvg_scale*h,
                                  nvg_scale*r, nvg_scale*r, 0.f, 0.f);
        };

        auto nvgLinearGradientS = [&](NVGcontext *ctx, float sx, float sy, float ex, float ey,
                                      NVGcolor icolor, NVGcolor ecolor) {
            return nvgLinearGradient(ctx, nvg_scale*sx, nvg_scale*sy, nvg_scale*ex, nvg_scale*ey,
                                     icolor, ecolor);
        };

        // Another limitation of nanovg is that rectangles are always axis-aligned.
        // We need to do some more coordinate transforms to generalize.
        float phi = atan2(m_b[1] - m_a[1], m_b[0] - m_a[0]);
        auto [sp, cp] = sincos(phi);
        float length = (1.f + 2.f*corner_radius)*norm(m_b - m_a);

        Matrix2f R  = Matrix2f(cp, -sp, sp, cp),
                 Ri = transpose(R),
                 Si = Matrix2f(rcp(length));

        Point2f ap = Si * Ri * m_a,
                bp = Si * Ri * m_b;
        ap -= Vector2f(corner_radius, 0.f);
        bp -= Vector2f(corner_radius, 0.f);

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

        float height = 1.f;
        nvgRectS(ctx, ap[0], ap[1], 1.f, -height, corner_radius);
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
        oss << "LinearSegment[" << std::endl
            << "  a = " << m_a << "," << std::endl
            << "  b = " << m_b << std::endl
            << "]";
        return oss.str();
    }

protected:
    Point2f m_a, m_b;

public:
    float gradient_start = 0.04f,
          gradient_width = 0.03f;
    float corner_radius = 0.04f;
};
