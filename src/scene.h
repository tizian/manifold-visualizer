#pragma once

#include <global.h>
#include <interaction.h>
#include <ray.h>

class Scene {
public:
    Scene();
    virtual ~Scene();

    void add_shape(std::shared_ptr<Shape> shape);

    Interaction ray_intersect(const Ray2f &ray_) const;

    void draw(NVGcontext *ctx) const;

    std::shared_ptr<Shape> shape(size_t k);

    std::shared_ptr<Shape> start_shape();
    std::shared_ptr<Shape> end_shape();
    std::shared_ptr<Shape> first_specular_shape();

protected:
    std::shared_ptr<Shape> m_start_shape, m_end_shape, m_first_specular_shape;
    std::vector<std::shared_ptr<Shape>> m_shapes;
    std::vector<std::shared_ptr<Shape>> m_draw_shapes;
};
