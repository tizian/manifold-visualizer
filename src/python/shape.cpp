#include <python/python.h>

#include <shape.h>
#include <shapes/circle.h>
#include <shapes/linear_segment.h>
#include <shapes/circle_segment.h>

#include <nanovg.h>

PYTHON_EXPORT(Shape) {
    auto shape = py::class_<Shape>(m, "Shape", py::dynamic_attr())
        .def_readwrite("name", &Shape::name)
        .def_readwrite("id", &Shape::id)
        .def_readwrite("type", &Shape::type)
        .def_readwrite("eta", &Shape::eta)
        .def_readwrite("hole", &Shape::hole)
        .def_readwrite("visible", &Shape::visible)
        .def_readwrite("parent", &Shape::parent)

        .def("flip", &Shape::flip)
        .def("add_hole", &Shape::add_hole,
             "hole"_a)
        .def("sample_position", &Shape::sample_position,
             "sample"_a)
        .def("project", &Shape::project,
             "p"_a)
        .def("draw", &Shape::draw,
             "ctx"_a, "hole"_a=false);

    py::enum_<Shape::Type>(shape, "Type", "Interaction Type", py::arithmetic())
        .value("Null", Shape::Type::Null)
        .value("Diffuse", Shape::Type::Diffuse)
        .value("Reflection", Shape::Type::Reflection)
        .value("Refraction", Shape::Type::Refraction);

    py::class_<Circle, Shape>(m, "Circle")
        .def(py::init<const Vector2f &, float>());

    py::class_<LinearSegment, Shape>(m, "LinearSegment")
        .def(py::init<const Point2f &, const Point2f &>());

    py::class_<CircleSegment, Shape>(m, "CircleSegment")
        .def(py::init<const Point2f &, const Point2f &, float>());
}
