#pragma once

#include <global.h>

class Shape;

struct Interaction {
    // Distance of the interaction along ray
    float rayt = Infinity;

    // Position of the interaction
    Point2f p;

    // Tangent
    Vector2f s;

    // Normal
    Vector2f n;

    // Position partial derivative w.r.t. the local parameterization
    Vector2f dp_du;

    // Normal partial derivative w.r.t. the local parameterization
    Vector2f dn_du;

    // Hit position in local parameterization
    float u;

    // Relative index of refraction at the interaction
    float eta = 1.f;

    // Associated shape
    const Shape *shape = nullptr;

    // String representation
    std::string to_string() const;
};
