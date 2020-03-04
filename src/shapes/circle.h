#pragma once

#include <shape.h>
#include <nanovg.h>

class Circle : public Shape {
public:
    Circle(const Point2f &center, float radius)
        : Shape(), m_center(center), m_radius(radius) {}

    Interaction sample_position(float sample) const override {
        float phi = 2.f*Pi*sample;
        auto [sp, cp] = sincos(phi);
        Point2f p_local(cp, sp);

        Interaction in;
        in.p = m_center + m_radius*p_local;
        in.n = p_local;
        in.s = Vector2f(-in.n[1], in.n[0]);
        in.dp_du = 2.f*Pi*Vector2f(-p_local[1], p_local[0]);
        float inv_radius = (m_flipped ? -1.f : 1.f) * rcp(m_radius);
        in.dn_du = in.dp_du*inv_radius;
        if (m_flipped) {
            in.n *= -1.f;
        }
        in.u = sample;
        in.shape = this;
        return in;
    }

    float project(const Point2f &p) const override {
        Vector2f d = p - m_center;
        float phi = atan2(d.y(), d.x());
        if (phi < 0.f) phi += 2.f*Pi;
        return phi*InvTwoPi;
    }

    std::pair<bool, float> ray_intersect(const Ray2f &ray) const override {
        float mint = ray.mint,
              maxt = ray.maxt;

        Vector2f o = Vector2f(ray.o) - m_center;
        Vector2f d(ray.d);

        float A = squared_norm(d),
              B = 2.0f * dot(o, d),
              C = squared_norm(o) - m_radius*m_radius;

        auto [solution_found, near_t, far_t] = solve_quadratic(A, B, C);

        bool out_bounds = !((near_t <= maxt) && (far_t >= mint)),
             in_bounds  = (near_t < mint) && (far_t > maxt);

        bool valid_intersection = solution_found && (!out_bounds) && (!in_bounds);
        float t = near_t < mint ? far_t : near_t;

        return { valid_intersection, t };
    }

    Interaction fill_interaction(const Ray2f &ray) const override {
        Interaction in;
        in.p = ray(in.rayt);
        in.p = m_center + normalize(in.p - m_center) * m_radius;
        in.n = normalize(in.p - m_center);
        in.s = Vector2f(-in.n[1], in.n[0]);
        Point2f p_local = in.p - m_center;
        in.dp_du = 2.f*Pi*Vector2f(-p_local[1], p_local[0]);

        float inv_radius = (m_flipped ? -1.f : 1.f) * rcp(m_radius);
        in.dn_du = in.dp_du * inv_radius;
        in.u = project(in.p);

        if (m_flipped) {
            in.n = -in.n;
        }
        return in;
    }

    void flip() override {
        m_flipped = !m_flipped;
    }

    void draw(NVGcontext *ctx, bool hole=false) const override {
        if (hole) {
            nvgCircle(ctx, m_center[0], m_center[1], m_radius);
            nvgPathWinding(ctx, NVG_HOLE);
        } else {
            Shape::draw(ctx);

            nvgBeginPath(ctx);
            nvgCircle(ctx, m_center[0], m_center[1], m_radius);

            for (size_t i=0; i<m_holes.size(); ++i) {
                m_holes[i]->draw(ctx, true);
            }

            nvgFill(ctx);
            nvgStroke(ctx);
        }
    }

    std::string to_string() const override {
        std::ostringstream oss;
        oss << "Circle[" << std::endl
            << "  radius = " << m_radius << "," << std::endl
            << "  center = " << m_center << std::endl
            << "]";
        return oss.str();
    }

protected:
    Vector2f m_center;
    float m_radius;
    bool m_flipped = false;
};
