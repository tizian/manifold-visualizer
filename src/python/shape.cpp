#include <python/python.h>

#include <shape.h>
#include <shapes/bezier_curve.h>
#include <shapes/circle.h>
#include <shapes/concave_segment.h>
#include <shapes/convex_segment.h>
#include <shapes/linear_segment.h>

#include <nanovg.h>

PYTHON_EXPORT(Shape) {
    auto shape = py::class_<Shape, std::shared_ptr<Shape>>(m, "Shape", py::dynamic_attr())
        .def_readwrite("name", &Shape::name)
        .def_readwrite("id", &Shape::id)
        .def_readwrite("type", &Shape::type)
        .def_readwrite("eta", &Shape::eta)
        .def_readwrite("hole", &Shape::hole)
        .def_readwrite("visible", &Shape::visible)
        .def_readwrite("parent", &Shape::parent)
        .def_readwrite("start", &Shape::start)
        .def_readwrite("end", &Shape::end)
        .def_readwrite("first_specular", &Shape::first_specular)

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
        .value("Emitter", Shape::Type::Emitter)
        .value("Reflection", Shape::Type::Reflection)
        .value("Refraction", Shape::Type::Refraction);

    py::class_<Circle, Shape, std::shared_ptr<Circle>>(m, "Circle")
        .def(py::init<const Vector2f &, float>());

    py::class_<ConcaveSegment, Shape, std::shared_ptr<ConcaveSegment>>(m, "ConcaveSegment")
        .def(py::init<const Point2f &, const Point2f &, float>())
        .def_readwrite("gradient_start", &ConcaveSegment::gradient_start)
        .def_readwrite("gradient_width", &ConcaveSegment::gradient_width);

    py::class_<ConvexSegment, Shape, std::shared_ptr<ConvexSegment>>(m, "ConvexSegment")
        .def(py::init<const Point2f &, const Point2f &, float, bool>(),
             "a"_a, "b"_a, "radius"_a, "alt"_a=false)
        .def_readwrite("gradient_start", &ConvexSegment::gradient_start)
        .def_readwrite("gradient_width", &ConvexSegment::gradient_width);

    py::class_<LinearSegment, Shape, std::shared_ptr<LinearSegment>>(m, "LinearSegment")
        .def(py::init<const Point2f &, const Point2f &>())
        .def_readwrite("gradient_start", &LinearSegment::gradient_start)
        .def_readwrite("gradient_width", &LinearSegment::gradient_width)
        .def_readwrite("height", &LinearSegment::height);

    py::class_<BezierCurve, Shape, std::shared_ptr<BezierCurve>>(m, "BezierCurve")
        .def(py::init<const std::vector<float> &, const std::vector<float> &>());
}
