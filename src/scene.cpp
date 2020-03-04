#include <scene.h>
#include <shape.h>

Scene::Scene() {}

Scene::~Scene() {}

void Scene::add_shape(std::shared_ptr<Shape> shape) {
    m_shapes.push_back(shape);
    if (shape->hole) {
        for (size_t k = 0; k < m_draw_shapes.size(); ++k) {
            if (m_draw_shapes[k]->name == shape->parent) {
                m_draw_shapes[k]->add_hole(shape);
            }
        }
    } else if (shape->visible) {
        m_draw_shapes.push_back(shape);
    }

    if (shape->start) {
        if (m_start_shape) {
            WARN("Scene: can only specify one start shape per scene!");
        }
        m_start_shape = shape;
    }

    if (shape->end) {
        if (m_end_shape) {
            WARN("Scene: can only specify one end shape per scene!");
        }
        m_end_shape = shape;
    }

    if (shape->first_specular) {
        if (m_first_specular_shape) {
            WARN("Scene: can only specify one shape as the \"first specular shape\" per scene!");
        }
        m_first_specular_shape = shape;
    }
}

Interaction Scene::ray_intersect(const Ray2f &ray_) const {
    bool found_hit = false;
    size_t idx = -1;
    float spline_t = -1.f;
    size_t spline_idx = -1;
    Ray2f ray(ray_);

    for (uint32_t k = 0; k < m_shapes.size(); ++k) {
        auto [hit_bbox, unused_0, unused_1] = m_shapes[k]->bbox.ray_intersect(ray);
        if (hit_bbox) {
            auto [hit, t, st, sidx] = m_shapes[k]->ray_intersect(ray);
            if (hit && t > ray.mint && t < ray.maxt) {
                found_hit = true;
                idx = k;
                spline_t = st;
                spline_idx = sidx;
                ray.maxt = t;
            }
        }
    }

    if (found_hit) {
        Interaction it = m_shapes[idx]->fill_interaction(ray, spline_t, spline_idx);
        it.rayt = ray.maxt;
        return it;
    }
    return Interaction();
}

void Scene::draw(NVGcontext *ctx) const {
    for (size_t k = 0; k < m_draw_shapes.size(); ++k) {
        m_draw_shapes[k]->draw(ctx);
    }
}

std::shared_ptr<Shape> Scene::shape(size_t k) {
    return m_shapes[k];
}

std::shared_ptr<Shape> Scene::start_shape() {
    return m_start_shape;
}

std::shared_ptr<Shape> Scene::end_shape() {
    return m_end_shape;
}

std::shared_ptr<Shape> Scene::first_specular_shape() {
    return m_first_specular_shape;
}