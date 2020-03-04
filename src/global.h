#pragma once

#include <iostream>
#include <string>
#include <vector>

#include <tinyformat.h>
#include <enoki/array.h>
#include <enoki/matrix.h>
using namespace enoki;

#define VERSION "0.0.1"

constexpr float Pi           = 3.14159265358979323846f;
constexpr float InvTwoPi     = 0.15915494309189533577f;
constexpr float Epsilon      = 1e-3f;
constexpr float Infinity     = std::numeric_limits<float>::infinity();
constexpr float MaxFloat     = std::numeric_limits<float>::max();

#include <nanovg.h>

static const NVGcolor COLOR_REFLECTION  = nvgRGB(240, 200, 91);
static const NVGcolor COLOR_REFRACTION  = nvgRGBA(128, 200, 255, 128);
static const NVGcolor COLOR_EMITTER     = nvgRGB(255, 255, 180);
static const NVGcolor COLOR_DIFFUSE     = nvgRGB(120, 120, 120);
static const NVGcolor COLOR_TRANSPARENT = nvgRGBA(0, 0, 0, 0);

#define TERM_COLOR_RED    "\x1B[31m"
#define TERM_COLOR_YELLOW "\x1B[33m"
#define TERM_COLOR_WHITE  "\x1B[37m"

#define LOG(str, ...)   std::cout << tfm::format(str "\n", ##__VA_ARGS__)
#define PRINT(str, ...) std::cout << tfm::format(str "\n", ##__VA_ARGS__)
#define INFO(str, ...)  std::cout << tfm::format("%s(%d): " str "\n", __FILE__, __LINE__, ##__VA_ARGS__)
#define WARN(str, ...)  std::cout << tfm::format(TERM_COLOR_YELLOW "%s(%d): " str "\n" TERM_COLOR_WHITE, __FILE__, __LINE__, ##__VA_ARGS__)
#define ERROR(str, ...)  throw std::runtime_error(tfm::format(TERM_COLOR_RED "\nError - %s(%d): " str "\n" TERM_COLOR_WHITE, __FILE__, __LINE__, ##__VA_ARGS__))

#define VARLOG(x)     (std::cout << #x << ": " << (x) << std::endl)
#define VARLOG2(x, y) (std::cout << #x << ": " << (x) << ", " << #y << ": " << (y) << std::endl)
#define VARLOG3(x, y, z) (std::cout << #x << ": " << (x) << ", " << #y << ": " << (y) << ", " << #z << ": " << (z) << std::endl)
#define VARLOG4(x, y, z, w) (std::cout << #x << ": " << (x) << ", " << #y << ": " << (y) << ", " << #z << ": " << (z) << ", " << #w << ": " << (w) << std::endl)

extern "C" {
    /* Dummy handle type -- will never be instantiated */
    typedef struct NVGcontext { int unused; } NVGcontext;
};

using Vector2f = Array<float, 2>;
using Vector2i = Array<int32_t, 2>;

using Point2f = Array<float, 2>;

using Matrix2f = Matrix<float, 2>;

inline float rad_to_deg(float rad) {
    return rad * (180 / Pi);
}

inline float deg_to_rad(float deg) {
    return deg * (Pi / 180);
}

inline float cross(const Vector2f &v0, const Vector2f &v1) {
    return v0[0]*v1[1] - v0[1]*v1[0];
}

template <typename T>
inline T lerp(float t, T a, T b) {
    return a + t * (b - a);
}

inline std::tuple<bool, float, float> solve_quadratic(float a, float b, float c) {
    /* Is this perhaps a linear equation? */
    bool linear_case = eq(a, 0.f);

    /* If so, we require b > 0 */
    bool active = !linear_case || (b > 0.f);

    /* Initialize solution with that of linear equation */
    float x0, x1;
    x0 = x1 = -c / b;

    /* Check if the quadratic equation is solvable */
    float discrim = fmsub(b, b, 4.f * a * c);
    active &= linear_case || (discrim >= 0);

    if (active) {
        float sqrt_discrim = sqrt(discrim);

        /* Numerically stable version of (-b (+/-) sqrt_discrim) / (2 * a)
         *
         * Based on the observation that one solution is always
         * accurate while the other is not. Finds the solution of
         * greater magnitude which does not suffer from loss of
         * precision and then uses the identity x1 * x2 = c / a
         */
        float temp = -0.5f * (b + copysign(sqrt_discrim, b));

        float x0p = temp / a,
              x1p = c / temp;

        /* Order the results so that x0 < x1 */
        float x0m = min(x0p, x1p),
              x1m = max(x0p, x1p);

        x0 = select(linear_case, x0, x0m);
        x1 = select(linear_case, x0, x1m);
    }

    return std::make_tuple(active, x0, x1);
}