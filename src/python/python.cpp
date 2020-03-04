#include <python/python.h>

PYTHON_DECLARE(Interaction);
PYTHON_DECLARE(Shape);

PYBIND11_MODULE(manifolds, m) {
    m.doc() = "manifold viewer python library";

    PYTHON_IMPORT(Interaction);
    PYTHON_IMPORT(Shape);
}
