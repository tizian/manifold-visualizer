#include <shape.h>
#include <interaction.h>
#include <nanovg.h>

Shape::~Shape() {}

Interaction Shape::sample_position(float sample) const {
    ERROR("Shape2::sample_position(): Not implemented!");
}

float Shape::project(const Point2f &p) const {
    ERROR("Shape2::project(): Not implemented!");
}

std::pair<bool, float> Shape::ray_intersect(const Ray2f &ray) const {
    ERROR("Shape2::ray_intersect(): Not implemented!");
}

Interaction Shape::fill_interaction(const Ray2f &ray) const {
    ERROR("Shape2::fill_interaction(): Not implemented!");
}

void Shape::draw(NVGcontext *ctx, bool hole) const {
    nvgStrokeWidth(ctx, 0.005);
    nvgStrokeColor(ctx, nvgRGB(0, 0, 0));

    if (type == Type::Reflection) {
        nvgFillColor(ctx, nvgRGB(235, 200, 91));
    } else if (type == Type::Refraction) {
        nvgFillColor(ctx, nvgRGBA(128, 200, 255, 128));
    } else {
        nvgFillColor(ctx, nvgRGB(180, 180, 180));
    }
}

std::string Shape::to_string() const {
    return "";
}