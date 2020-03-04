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
}
