#include <python/python.h>

PYTHON_DECLARE(Ray2f);
PYTHON_DECLARE(Interaction);
PYTHON_DECLARE(Shape);
PYTHON_DECLARE(Scene);

PYBIND11_MODULE(manifolds, m) {
    m.doc() = "manifold viewer python library";

    PYTHON_IMPORT(Ray2f);
    PYTHON_IMPORT(Interaction);
    PYTHON_IMPORT(Shape);
    PYTHON_IMPORT(Scene);
}
