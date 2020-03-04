#include <python/python.h>

#include <interaction.h>
#include <shape.h>

PYTHON_EXPORT(Interaction) {
    py::class_<Interaction>(m, "Interaction", "2D Interaction record", py::dynamic_attr())
        .def(py::init<>())
        .def_readwrite("rayt", &Interaction::rayt)
        .def_readwrite("p", &Interaction::p)
        .def_readwrite("n", &Interaction::n)
        .def_readwrite("dp_du", &Interaction::dp_du)
        .def_readwrite("dn_du", &Interaction::dn_du)
        .def_readwrite("s", &Interaction::s)
        .def_readwrite("ds_du", &Interaction::ds_du)
        .def_readwrite("n_offset", &Interaction::n_offset)
        .def_readwrite("u", &Interaction::u)
        .def_readwrite("eta", &Interaction::eta)
        .def_readonly("shape", &Interaction::shape)
        .def("is_valid", &Interaction::is_valid)
        .def("__repr__", &Interaction::to_string)
        .def("copy", [](const Interaction &in) {
            Interaction new_in;
            new_in.rayt = in.rayt;
            new_in.p = in.p;
            new_in.n = in.n;
            new_in.dp_du = in.dp_du;
            new_in.dn_du = in.dn_du;
            new_in.s = in.s;
            new_in.ds_du = in.ds_du;
            new_in.n_offset = in.n_offset;
            new_in.u = in.u;
            new_in.eta = in.eta;
            new_in.shape = in.shape;
            return new_in;
        });
}
