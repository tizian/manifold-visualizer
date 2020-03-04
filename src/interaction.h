#pragma once

#include <global.h>

class Shape;

struct Interaction {
    // Distance of the interaction along ray
    float rayt = Infinity;

    // Position of the interaction
    Point2f p;

    // Normal
    Vector2f n;

    // Position partial derivative w.r.t. the local parameterization
    Vector2f dp_du;

    // Normal partial derivative w.r.t. the local parameterization
    Vector2f dn_du;

    // Tangent
    Vector2f s;

    // Tangent derivative
    Vector2f ds_du;

    // Offset normal (for rough variations)
    Vector2f n_offset;

    // Hit position in local parameterization
    float u;

    // Relative index of refraction at the interaction
    float eta;

    // Associated shape
    const Shape *shape = nullptr;

    // String representation
    std::string to_string() const;

    bool is_valid() const { return rayt < Infinity; }
};
