#pragma once

#include <global.h>

struct Ray2f {
    Point2f o;
    Vector2f d;
    float mint = Epsilon;
    float maxt = Infinity;

    Ray2f(const Point2f &o, const Vector2f &d)
        : o(o), d(d) {}

    Ray2f(const Point2f &o, const Vector2f &d, float mint, float maxt)
        : o(o), d(d), mint(mint), maxt(maxt) {}

    Point2f operator() (float t) const { return fmadd(d, t, o); }

    std::string to_string() const {
        std::ostringstream oss;
        oss << "Ray2f[" << std::endl
            << "  o = " << o << "," << std::endl
            << "  d = " << d << "," << std::endl
            << "  mint = " << mint << "," << std::endl
            << "  maxt = " << maxt << "," << std::endl
            << "]";
        return oss.str();
    }
};
