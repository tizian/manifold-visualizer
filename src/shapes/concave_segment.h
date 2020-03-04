#pragma once

#include <shape.h>
#include <nanovg.h>

class ConcaveSegment : public Shape {
public:
    ConcaveSegment(const Point2f &a, const Point2f &b, float arc_radius)
        : Shape(), m_a(a), m_b(b), m_arc_radius(arc_radius) {
            name = "ConcaveSegment";

            Vector2f dir = m_b - m_a;
            float length = norm(dir);
            Vector2f n(-dir[1], dir[0]);
            n *= rcp(length);
            float phi = atan2(n.y(), n.x());
            if (phi < 0.f) phi += 2.f*Pi;

            float d_phi = asin(0.5f*length*rcp(m_arc_radius));
            m_phi_0 = phi - d_phi + Pi;
            m_phi_1 = phi + d_phi - Pi + 2.f*Pi;

            float offset = safe_sqrt(sqr(m_arc_radius) - sqr(0.5f*length));
            m_center = 0.5f*(m_a + m_b) + n*offset;

            size_t K = 30;
            bbox = BoundingBox2f();
            for (size_t k = 0; k < K; ++k) {
                float t = k * rcp(float(K-1));
                Interaction it = sample_position(t);
                bbox.expand(it.p);
            }
        }

    Interaction sample_position(float sample) const override {
        float phi = m_phi_0 + (m_phi_1 - m_phi_0)*sample;
        auto [sp, cp] = sincos(phi);
        Point2f p_local(cp, sp);

        Interaction in;
        in.rayt = 0;
        in.p = m_center + m_arc_radius*p_local;
        in.n = -p_local;
        in.dp_du = (m_phi_1 - m_phi_0)*Vector2f(-p_local[1], p_local[0]);
        float inv_radius = -rcp(m_arc_radius);
        in.dn_du = in.dp_du*inv_radius;
        in.u = sample;
        in.s = Vector2f(-in.n[1], in.n[0]);
        in.ds_du = Vector2f(-in.dn_du[1], in.dn_du[0]);
        in.shape = this;
        return in;
    }

    std::tuple<float, float, float> angle_test(const Point2f &p) const {
        // Compute extent of valid angles
        Vector2f dir = m_b - m_a;
        float length = norm(dir);
        float d_phi = asin(0.5f*length*rcp(m_arc_radius));

        // Project to circle
        Vector2f d = normalize(p - m_center);
        float phi = atan2(d.y(), d.x());
        if (phi < 0.f) phi += 2.f*Pi;

        // Rotate everything s.t. it alignes with the normal of [A, B]
        Vector2f n(-dir[1], dir[0]);
        n *= rcp(length);
        float phi_n = atan2(-n.y(), -n.x());
        if (phi_n < 0.f) phi_n += 2.f*Pi;
        float phi_p = phi - phi_n;

        // Make sure, phi_p is in [-Pi, +Pi)
        phi_p = fmod(phi_p + Pi, 2.f*Pi);
        if (phi_p < 0.f) phi_p += 2.f*Pi;
        phi_p -= Pi;

        return std::make_tuple(phi, phi_p, d_phi);
    }

    float project(const Point2f &p) const override {
        auto [phi, phi_p, d_phi] = angle_test(p);
        if (phi_p > d_phi) return 1.f;
        if (phi_p < -d_phi) return 0.f;
        return (phi - m_phi_0) / (m_phi_1 - m_phi_0);
    }

    std::tuple<bool, float, float, size_t> ray_intersect(const Ray2f &ray) const override {
        float mint = ray.mint,
              maxt = ray.maxt;

        Vector2f o = Vector2f(ray.o) - m_center;
        Vector2f d(ray.d);

        float A = squared_norm(d),
              B = 2.0f * dot(o, d),
              C = squared_norm(o) - m_arc_radius*m_arc_radius;

        auto [solution_found, near_t, far_t] = solve_quadratic(A, B, C);

        bool out_bounds = !((near_t <= maxt) && (far_t >= mint)),
             in_bounds  = (near_t < mint) && (far_t > maxt);

        bool valid_intersection = solution_found && (!out_bounds) && (!in_bounds);
        if (!valid_intersection) {
            return { false, Infinity, -1.f, 0 };
        }

        if (near_t >= mint) {
            // Test near hit
            Point2f p = ray(near_t);
            p = m_center + normalize(p - m_center) * m_arc_radius;
            auto [unused, phi_p, d_phi] = angle_test(p);
            if (abs(phi_p) < d_phi) {
                return { true, near_t, -1.f, 0 };
            }
        }
        // Test far hit
        Point2f p = ray(far_t);
        p = m_center + normalize(p - m_center) * m_arc_radius;
        auto [unused, phi_p, d_phi] = angle_test(p);
        if (abs(phi_p) < d_phi) {
            return { true, far_t, -1.f, 0 };
        }

        return { false, Infinity, -1.f, 0 };
    }

    Interaction fill_interaction(const Ray2f &ray, float spline_t, size_t spline_idx) const override {
        Interaction in;
        in.rayt = ray.maxt;
        in.p = ray(in.rayt);
        in.p = m_center + normalize(in.p - m_center) * m_arc_radius;
        in.n = -normalize(in.p - m_center);
        Point2f p_local = in.p - m_center;
        in.dp_du = (m_phi_1 - m_phi_0)*Vector2f(-p_local[1], p_local[0]);
        in.dn_du = -in.dp_du * rcp(m_arc_radius);
        in.u = project(in.p);
        in.s = Vector2f(-in.n[1], in.n[0]);
        in.ds_du = Vector2f(-in.dn_du[1], in.dn_du[0]);
        in.shape = this;
        return in;
    }

    void draw(NVGcontext *ctx, bool hole=false) const override {
        if (hole) return;

        Shape::draw(ctx);
        nvgSave(ctx);

        NVGcolor fill_color;
        if (type == Type::Reflection) {
            fill_color = COLOR_REFLECTION;
        } else if (type == Type::Refraction) {
            fill_color = COLOR_REFRACTION;
        } else if (type == Type::Emitter) {
            fill_color = COLOR_EMITTER;
        } else {
            fill_color = COLOR_DIFFUSE;
        }

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
        if (phi < 0.f) phi += 2.f*Pi;
        auto [sp, cp] = sincos(phi);
        float length = norm(m_b - m_a);

        Matrix2f R  = Matrix2f(cp, -sp, sp, cp),
                 Ri = transpose(R),
                 Si = Matrix2f(rcp(length));

        Point2f ap = Si * Ri * m_a,
                bp = Si * Ri * m_b;
        float arc_radius = rcp(length) * m_arc_radius;

        nvgStrokeWidth(ctx, nvg_scale*0.007f*rcp(length));
        nvgRotate(ctx, phi);
        nvgScale(ctx, length, length);

        // Set up gradients
        Point2f p0 = 0.5f*(ap + bp),
                p1 = p0 - Vector2f(0.f, gradient_start),
                p2 = p1 - Vector2f(0.f, gradient_width);
        auto fill_grad   = nvgLinearGradientS(ctx, p1[0], p1[1], p2[0], p2[1],
                                              fill_color, COLOR_TRANSPARENT);
        auto stroke_grad = nvgLinearGradientS(ctx, p1[0], p1[1], p2[0], p2[1],
                                              nvgRGBA(0, 0, 0, 255), COLOR_TRANSPARENT);
        nvgFillPaint(ctx, fill_grad);
        nvgStrokePaint(ctx, stroke_grad);

        nvgBeginPath(ctx);

        // Main arc
        float offset = safe_sqrt(sqr(arc_radius) - 0.25f);
        Point2f c_main = Point2f(ap[0] + 0.5f, bp[1] + offset);
        float alpha = asin(0.5f*rcp(arc_radius));

        // Smaller arcs left and right to transition smoothly to vertical
        Vector2f n_left = normalize(ap - c_main),
                 n_right = normalize(bp - c_main);
        Point2f c_left = ap + corner_radius*n_left,
                c_right = bp + corner_radius*n_right;
        float beta_left = atan2(-n_left.y(), -n_left.x()),
              beta_right = atan2(-n_right.y(), -n_right.x());
        if (beta_left < 0.f) beta_left += 2.f*Pi;
        if (beta_right < 0.f) beta_right += 2.f*Pi;

        // Rest of shape
        Point2f d_left = c_left - Vector2f(corner_radius, 0.f),
                e_left = d_left - Vector2f(0.f, 1.f),
                d_right = c_right + Vector2f(corner_radius, 0.f),
                e_right = d_right - Vector2f(0.f, 1.f);

        nvgMoveToS(ctx, d_right[0], d_right[1]);
        nvgLineToS(ctx, e_right[0], e_right[1]);
        nvgLineToS(ctx, e_left[0], e_left[1]);
        nvgLineToS(ctx, d_left[0], d_left[1]);

        if (abs(beta_left - Pi) > Epsilon)
            nvgArcS(ctx, c_left[0], c_left[1], corner_radius, Pi, beta_left, NVG_CCW);
        nvgArcS(ctx, c_main[0], c_main[1], arc_radius, 1.5f*Pi - alpha, 1.5f*Pi + alpha, NVG_CW);
        if (abs(beta_right) > Epsilon)
            nvgArcS(ctx, c_right[0], c_right[1], corner_radius, beta_right, 0.f, NVG_CCW);

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
        oss << "ConcaveSegment[" << std::endl
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
    float gradient_start = 0.08f,
          gradient_width = 0.03f;
    float corner_radius = 0.02f;
};
