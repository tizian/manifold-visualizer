#pragma once

#include <global.h>
#include <ray.h>

struct BoundingBox2f {
    Point2f min, max;

    BoundingBox2f() { reset(); }

    BoundingBox2f(const Point2f &min, const Point2f &max)
        : min(min), max(max) {}

    bool valid() const {
        return all(max >= min);
    }

    bool collapsed() const {
        return any(eq(min, max));
    }

    void reset() {
        min =  Infinity;
        max = -Infinity;
    }

    void expand(const Point2f &p) {
        min = enoki::min(min, p);
        max = enoki::max(max, p);
    }

    void expand(const BoundingBox2f &bbox) {
        min = enoki::min(min, bbox.min);
        max = enoki::max(max, bbox.max);
    }

    std::tuple<bool, float, float> ray_intersect(const Ray2f &ray) {
        bool active = all(neq(ray.d, zero<Vector2f>()) || ((ray.o > min) || (ray.o < max)));

        Vector2f t1 = (min - ray.o) * rcp(ray.d),
                 t2 = (max - ray.o) * rcp(ray.d);

        Vector2f t1p = enoki::min(t1, t2),
                 t2p = enoki::max(t1, t2);

        float mint = hmax(t1p),
              maxt = hmin(t2p);

        active = active && (maxt >= mint);

        return std::make_tuple(active, mint, maxt);
    }

    std::string to_string() const {
        std::ostringstream oss;
        oss << "BoundingBox2f";
        if (!valid()) {
            oss << "[invalid]";
        } else {
            oss << "[" << std::endl
                << "  min = " << min << "," << std::endl
                << "  max = " << max << std::endl
                << "]";
        }
        return oss.str();
    }
};
