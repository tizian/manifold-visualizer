#include <python/python.h>

#include <ray.h>

PYTHON_EXPORT(Ray2f) {
    py::class_<Ray2f>(m, "Ray2f", "2D Ray", py::dynamic_attr())
        .def(py::init<Point2f, Vector2f>())
        .def(py::init<Point2f, Vector2f, float, float>())
        .def_readwrite("o", &Ray2f::o)
        .def_readwrite("d", &Ray2f::d)
        .def_readwrite("mint", &Ray2f::mint)
        .def_readwrite("maxt", &Ray2f::maxt)
        .def("__repr__", &Ray2f::to_string);
}
