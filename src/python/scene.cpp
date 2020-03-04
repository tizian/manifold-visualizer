#include <python/python.h>

#include <scene.h>
#include <shape.h>

PYTHON_EXPORT(Scene) {
    py::class_<Scene>(m, "Scene", "Scene", py::dynamic_attr())
        .def(py::init<>())
        .def("add_shape", &Scene::add_shape)
        .def("ray_intersect", &Scene::ray_intersect)
        .def("draw", &Scene::draw)
        .def("shape", &Scene::shape)
        .def("start_shape", &Scene::start_shape)
        .def("end_shape", &Scene::end_shape)
        .def("first_specular_shape", &Scene::first_specular_shape);

    // This function is not exposed by the nanogui Python API --- so do it here instead.
    m.def("nvgCurrentTransform",
         [](NVGcontext *ctx) {
             float v[6];
             nvgCurrentTransform(ctx, v);
             return std::make_tuple(v[0], v[1], v[2], v[3], v[4], v[5]);
         }
    );
}
