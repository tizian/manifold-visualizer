#include <shape.h>
#include <interaction.h>
#include <nanovg.h>

Shape::~Shape() {}

Interaction Shape::sample_position(float sample) const {
    ERROR("Shape::sample_position(): Not implemented!");
}

float Shape::project(const Point2f &p) const {
    ERROR("Shape::project(): Not implemented!");
}

std::tuple<bool, float, float, size_t> Shape::ray_intersect(const Ray2f &ray) const {
    ERROR("Shape::ray_intersect(): Not implemented!");
}

Interaction Shape::fill_interaction(const Ray2f &ray, float spline_t, size_t spline_idx) const {
    ERROR("Shape::fill_interaction(): Not implemented!");
}

void Shape::draw(NVGcontext *ctx, bool hole) const {
    nvgStrokeWidth(ctx, 0.007f);
    nvgStrokeColor(ctx, nvgRGB(0, 0, 0));

    if (type == Type::Reflection) {
        nvgFillColor(ctx, COLOR_REFLECTION);
    } else if (type == Type::Refraction) {
        nvgFillColor(ctx, COLOR_REFRACTION);
    } else if (type == Type::Emitter) {
        nvgFillColor(ctx, COLOR_EMITTER);
    } else {
        nvgFillColor(ctx, COLOR_DIFFUSE);
    }
}

std::string Shape::to_string() const {
    return "";
}