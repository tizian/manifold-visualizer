#pragma once

#include <global.h>

template <typename T, typename Predicate>
int find_interval(T size, const Predicate &pred) {
    T first = 0, len = size;
    while (len > 0) {
        T half = len >> 1, middle = first + half;
        // Bisect range based on value of pred at middle
        if (pred(middle)) {
            first = middle + 1;
            len -= half + 1;
        } else {
            len = half;
        }
    }
    return clamp(first - 1, T(0), size - 2);
}

class DiscreteDistribution {
public:
    DiscreteDistribution() {}

    DiscreteDistribution(const float *f, int n) : m_func(f, f + n), m_cdf(n + 1) {
        m_cdf[0] = 0.f;
        for (int i = 1; i < n + 1; ++i) {
            m_cdf[i] = m_cdf[i - 1] + m_func[i - 1];
        }

        m_normalization = 1.f / m_cdf[n];

        for (int i = 1; i < n + 1; ++i) {
            m_cdf[i] *= m_normalization;
        }
    }

    inline float operator[](int i) const {
        return m_cdf[i+1] - m_cdf[i];
    }

    inline float cdf(int i) const {
        return m_cdf[i];
    }

    inline int sample(float u) const {
        return find_interval(int(m_cdf.size()), [&](int index) { return m_cdf[index] <= u; });
    }

    inline int sample(float u, float &pdf) const {
        int offset = sample(u);
        pdf = m_func[offset] * m_normalization;
        return offset;
    }

    inline int sample_reuse(float &u) const {
        int offset = sample(u);
        u = (u - m_cdf[offset]) / (m_cdf[offset + 1] - m_cdf[offset]);
        return offset;
    }

    inline int sample_reuse(float &u, float &pdf) {
        int offset = sample(u, pdf);
        u = (u - m_cdf[offset]) / (m_cdf[offset + 1] - m_cdf[offset]);
        return offset;
    }

    inline float normalization() const { return m_normalization; }

private:
    std::vector<float> m_func, m_cdf;
    float m_normalization;
};