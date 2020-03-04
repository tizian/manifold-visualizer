#pragma once

#include <shape.h>
#include <ddistr.h>
#include <nanovg.h>

#define SPLINE_DISCRETIZATION 15

struct BezierSpline {
    Point2f p[4];   // Control points for a cubic bezier spline

    BoundingBox2f bbox() const {
        BoundingBox2f result;
        for (int i=0; i<4; ++i)
            result.expand(p[i]);
        result.min -= Vector2f(Epsilon);
        result.min += Vector2f(Epsilon);
        return result;
    }

    Point2f eval(float t) const {
        float tmp  = 1.f - t,
              tmp2 = tmp * tmp,
              tmp3 = tmp * tmp2,
              t2 = t * t,
              t3 = t * t2;
        // Cubic Bezier curve (explicit form)
        return tmp3 * p[0] + 3.f*tmp2*t * p[1] + 3.f*tmp*t2 * p[2] + t3 * p[3];
    }

    Vector2f eval_tangent(float t) const {
        float tmp  = 1.f - t,
              tmp2 = tmp * tmp,
              t2 = t * t;
        // First derivative of cubic Bezier curve
        return 3.f*tmp2 * (p[1] - p[0]) + 6.f*tmp*t * (p[2] - p[1]) + 3.f*t2 * (p[3] - p[2]);
    }

    Vector2f eval_curvature(float t) const {
        float tmp = 1.f - t;
        return 6.f*tmp * (p[2] - 2.f*p[1] + p[0]) + 6.f*t*(p[3] - 2.f*p[2] + p[1]);
    }

    void flip() {
        std::reverse(&p[0], &p[4]);
    }

    float length() const {
        const int n_steps = SPLINE_DISCRETIZATION;
        float length = 0;
        for (int i = 0; i < n_steps; ++i)
            length += norm(eval_tangent(float(i) / (n_steps-1)));
        return length / n_steps;
    }

    Interaction fill_interaction(float u) const {
        Vector2f P = eval(u);
        Vector2f T = eval_tangent(u);
        Vector2f N(-T[1], T[0]);
        float scale = 1.0f / std::sqrt(dot(N, N));
        N *= scale;

        // Second derivative of cubic Bezier curve
        Vector2f dN = eval_curvature(u);
        dN *= scale;
        dN = Vector2f(-dN[1], dN[0]);

        Interaction it;
        it.p = P;
        it.n = N;
        it.dp_du = T;
        it.dn_du = dN;
        it.u = u;
        it.s = Vector2f(-it.n[1], it.n[0]);
        it.ds_du = Vector2f(-it.dn_du[1], it.dn_du[0]);
        return it;
    }

    Interaction sample_position(float sample) const {
        return fill_interaction(sample);
    }

    std::tuple<bool, float, float> ray_intersect(const Ray2f &ray) const {
        const int n_steps = SPLINE_DISCRETIZATION;
        bool success = false;
        float t = Infinity;
        float spline_t;

        for (int i = 0; i < n_steps; ++i) {
            float t0 = float(i)   / n_steps,
                  t1 = float(i+1) / n_steps;
            Point2f p0 = eval(t0), p1 = eval(t1);
            Vector2f d(p1 - p0);
            float len = norm(d);
            if (len == 0.f)
                continue;
            d /= len;

            Vector2f n(-d.y(), d.x());

            float dp = dot(n, ray.d);
            if (dp == 0)
                continue;

            float tp = dot(n, p0 - ray.o) / dp;
            float proj = dot(ray(tp)-p0, d) / len;

            if (tp >= ray.mint && tp <= ray.maxt && tp < t && proj >= 0 && proj <= 1) {
                spline_t = t0*(1-proj) + t1*proj;
                success = true;
                t = tp;
            }
        }

        if (success) {
            for (int i = 0; i < 3; ++i) {
                // Do a few 2D Newton iterations to converge on the root
                Point2f  p_spline = eval(spline_t);
                Vector2f dp_spline = eval_tangent(spline_t);
                Point2f  p_ray = ray(t);
                Vector2f dp_ray = ray.d;

                Matrix2f Jf(dp_spline.x(), -dp_ray.x(),
                            dp_spline.y(), -dp_ray.y());
                Vector2f b(p_spline.x() - p_ray.x(),
                           p_spline.y() - p_ray.y());

                Vector2f x = inverse(Jf) * b;

                spline_t -= x[0];
                t        -= x[1];
            }
            if (t < ray.mint || t > ray.maxt || spline_t < 0 || spline_t > 1)
                return { false, t, spline_t };
        }

        return { success, t, spline_t };
    }

    std::tuple<Point2f, float> project(const Point2f &p) const {
        const int n_steps = SPLINE_DISCRETIZATION;
        float d2 = Infinity;
        float t;

        for (int i = 0; i < n_steps; ++i) {
            float t0 = float(i) / (n_steps - 1);
            Point2f p0 = eval(t0);

            float d20 = squared_norm(p0 - p);
            if (d20 < d2) {
                d2 = d20;
                t = t0;
            }
        }

        for (int i = 0; i < 3; ++i) {
            // Do a few 1D Newton iterations to converge on minimum (i.e. root of first derivative)
            Point2f    p_spline = eval(t);
            Vector2f  dp_spline = eval_tangent(t);
            Vector2f d2p_spline = eval_curvature(t);

            float df = 2.f*(dot(p_spline, dp_spline) - dot(p, dp_spline));
            float d2f = 2.f*(dot(p_spline, d2p_spline) + dot(dp_spline, dp_spline) - dot(p, d2p_spline));

            float dt = rcp(d2f) * df;
            t -= dt;
        }
        t = max(0.f, min(1.f, t));
        return { eval(t), t };
    }
};


class BezierCurve : public Shape {
public:
    BezierCurve(const std::vector<float> &pts_x,
                const std::vector<float> &pts_y)
        : Shape() {
        name = "BezierCurve";

        if (pts_x.size() != pts_y.size()) {
            WARN("BezierCurve: Number of control points in x and y should be the same.");
        }
        if (pts_x.size() % 4 != 0) {
            WARN("BezierCurve: Number of control points should be multiple of 4.");
        }

        // Fill in control points
        size_t n_splines = pts_x.size() / 4;
        for (size_t i = 0; i < n_splines; ++i) {
            BezierSpline spline;
            for (size_t k = 0; k < 4; ++k) {
                spline.p[k] = Point2f(pts_x[4*i + k], pts_y[4*i + k]);
            }
            m_splines.push_back(spline);
        }

        // Precompute lengths for sampling
        std::vector<float> lengths;
        for (size_t i = 0; i < n_splines; ++i) {
            lengths.push_back(m_splines[i].length());
        }
        m_length_map = DiscreteDistribution(lengths.data(), lengths.size());

        // Precompute bounding box
        bbox = BoundingBox2f();
        for (size_t i = 0; i < m_splines.size(); i++) {
            bbox.expand(m_splines[i].bbox());
        }
    }

    Interaction sample_position(float sample) const override {
        int spline_idx = m_length_map.sample_reuse(sample);
        const BezierSpline &spline = m_splines[spline_idx];
        Interaction it = spline.sample_position(sample);
        it.u = sample;
        it.shape = this;
        return it;
    }

    float project(const Point2f &p) const override {
        float d2 = Infinity;
        float t;
        size_t idx;

        for (size_t i = 0; i < m_splines.size(); ++i) {
            auto [p0, t0] = m_splines[i].project(p);
            float d20 = squared_norm(p0 - p);
            if (d20 < d2) {
                d2 = d20;
                t = t0;
                idx = i;
            }
        }

        float t0 = m_length_map.cdf(idx),
              t1 = m_length_map.cdf(idx + 1);
        return t0*(1.f - t) + t1*t;
    }

    std::tuple<bool, float, float, size_t> ray_intersect(const Ray2f &ray_) const override {
        bool found_hit = false;

        size_t idx = -1;
        float spline_t = -1.f;
        Ray2f ray(ray_);

        for (uint32_t k = 0; k < m_splines.size(); ++k) {
            auto [hit_bbox, unused_0, unused_1] = m_splines[k].bbox().ray_intersect(ray);
            if (hit_bbox) {
                auto [hit, t, st] = m_splines[k].ray_intersect(ray);
                if (hit && t > ray.mint && t < ray.maxt) {
                    found_hit = true;
                    idx = k;
                    spline_t = st;
                    ray.maxt = t;
                }
            }
        }

        return { found_hit, ray.maxt, spline_t, idx };
    }

    Interaction fill_interaction(const Ray2f &ray, float spline_t, size_t spline_idx) const override {
        Interaction it = m_splines[spline_idx].fill_interaction(spline_t);
        it.shape = this;
        return it;
    }

    void flip() override {
        std::reverse(m_splines.begin(), m_splines.end());
        for (size_t i = 0; i < m_splines.size(); ++i) {
            m_splines[i].flip();
        }
    }

    void draw(NVGcontext *ctx, bool hole=false) const override {
        if (m_splines.size() == 0) return;

        if (hole) {
            nvgMoveTo(ctx, m_splines[0].p[0].x(), m_splines[0].p[0].y());
            nvgPathWinding(ctx, NVG_HOLE);
            for (size_t i = 0; i < m_splines.size(); ++i) {
                const BezierSpline &s = m_splines[i];
                nvgBezierTo(ctx, s.p[1].x(), s.p[1].y(),
                                 s.p[2].x(), s.p[2].y(),
                                 s.p[3].x(), s.p[3].y());
                nvgPathWinding(ctx, NVG_HOLE);
            }
        } else {
            nvgSave(ctx);
            Shape::draw(ctx);

            nvgBeginPath(ctx);
            nvgMoveTo(ctx, m_splines[0].p[0].x(), m_splines[0].p[0].y());
            for (size_t i = 0; i < m_splines.size(); ++i) {
                const BezierSpline &s = m_splines[i];
                nvgBezierTo(ctx, s.p[1].x(), s.p[1].y(),
                                 s.p[2].x(), s.p[2].y(),
                                 s.p[3].x(), s.p[3].y());
            }

            for (size_t i=0; i<m_holes.size(); ++i) {
                m_holes[i]->draw(ctx, true);
            }

            nvgFill(ctx);
            nvgStroke(ctx);

            nvgRestore(ctx);
        }
    }

    std::string to_string() const override {
        std::ostringstream oss;
        oss << "BezierCurve[]" << std::endl;
        return oss.str();
    }

protected:
    std::vector<BezierSpline> m_splines;
    DiscreteDistribution m_length_map;
};
