#include <interaction.h>

std::string Interaction::to_string() const {
    std::ostringstream oss;
    oss << "Interaction[" << std::endl
        << "  rayt = " << rayt << "," << std::endl
        << "  p = " << p << "," << std::endl
        << "  s = " << s << "," << std::endl
        << "  n = " << n << "," << std::endl
        << "  dp_du = " << dp_du << "," << std::endl
        << "  dn_du = " << dn_du << "," << std::endl
        << "  u = " << u << "," << std::endl
        << "  eta = " << eta << "," << std::endl
        // << "  shape = " << (shape == nullptr ? "null" : string::indent(shape->to_string())) << "," << std::endl
        << "]";
    return oss.str();
}
