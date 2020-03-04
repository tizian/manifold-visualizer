#pragma once

#include <global.h>
#include <interaction.h>
#include <bbox.h>
#include <ray.h>

struct NVGcontext;

class Shape {
public:
    virtual ~Shape();

    // Sample surface interaction from local parameterization
    virtual Interaction sample_position(float sample) const;

    // Give local parameterization of closest point on the shape
    virtual float project(const Point2f &p) const;

    // Intersect shape with ray
    virtual std::tuple<bool, float, float, size_t> ray_intersect(const Ray2f &ray) const;

    // Fill hit information after successful ray intersect
    virtual Interaction fill_interaction(const Ray2f &ray, float spline_t, size_t spline_idx) const;

    // Flip orientation and normals
    virtual void flip() {}

    // Draw this shape in the window
    virtual void draw(NVGcontext *ctx, bool hole=false) const;

    // String representation
    virtual std::string to_string() const;

public:
    std::string name;
    int id;

    BoundingBox2f bbox;

    enum Type {
        Null,
        Diffuse,
        Emitter,
        Refraction,
        Reflection
    };

    Type type;
    float eta = 1.f;

    bool start = false;
    bool first_specular = false;
    bool end = false;

    bool hole = false;
    bool visible = true;
    std::string parent;
    void add_hole(std::shared_ptr<Shape> hole) {
        m_holes.push_back(hole);
    }

protected:
    std::vector<std::shared_ptr<Shape>> m_holes;
};
