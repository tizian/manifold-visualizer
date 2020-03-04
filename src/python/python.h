#pragma once

#include <global.h>

#include <pybind11/pybind11.h>
#include <pybind11/operators.h>
#include <pybind11/complex.h>
#include <pybind11/stl.h>

namespace py = pybind11;
using namespace py::literals;

#include <enoki/python.h>
using namespace enoki;

#define PYTHON_EXPORT(name) \
    void python_export_##name(py::module &m)
#define PYTHON_DECLARE(name) \
    extern void python_export_##name(py::module &)
#define PYTHON_IMPORT(name) \
    python_export_##name(m)
