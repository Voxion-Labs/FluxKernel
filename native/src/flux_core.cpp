#define FLUX_BUILDING_DLL
#include "flux/flux_core.h"

#include <string_view>
#include <algorithm>
#include <numeric>
#include <span>
#include <vector>
#include <filesystem>
#include <system_error>

static constexpr const char* NATIVE_VERSION = "FluxKernel-Native-C++20-v0.3.0";

namespace fs = std::filesystem;

extern "C" {

FLUX_API const char* flux_version(void) {
    return NATIVE_VERSION;
}

FLUX_API int32_t flux_compute(int32_t a, int32_t b) {
    int64_t result = static_cast<int64_t>(a) * static_cast<int64_t>(b);
    if (result > INT32_MAX) return INT32_MAX;
    if (result < INT32_MIN) return INT32_MIN;
    return static_cast<int32_t>(result);
}

FLUX_API int32_t flux_sandbox_available(void) {
#if defined(__linux__) || defined(_WIN32)
    return 1;
#else
    return 0;
#endif
}

FLUX_API int64_t flux_diff_distance(const char* a, size_t len_a, const char* b, size_t len_b) {
    if (!a || !b) return -1;

    std::string_view sva(a, len_a);
    std::string_view svb(b, len_b);

    if (sva == svb) return 0;

    size_t min_len = std::min(len_a, len_b);
    size_t diff_bytes = 0;

    for (size_t i = 0; i < min_len; ++i) {
        if (sva[i] != svb[i]) {
            diff_bytes++;
        }
    }

    diff_bytes += (std::max(len_a, len_b) - min_len);
    return static_cast<int64_t>(diff_bytes);
}

FLUX_API float flux_fast_vector_dot(const float* a, const float* b, size_t len) {
    if (!a || !b || len == 0) return 0.0f;

    float sum = 0.0f;
    // Auto-vectorizable reduction loop
    for (size_t i = 0; i < len; ++i) {
        sum += a[i] * b[i];
    }
    return sum;
}

FLUX_API int32_t flux_sandbox_verify_path(const char* base_dir, const char* target_path) {
    if (!base_dir || !target_path) return 0;

    std::error_code ec;
    fs::path base = fs::weakly_canonical(fs::path(base_dir), ec);
    if (ec) return 0;

    fs::path target = fs::weakly_canonical(fs::path(target_path), ec);
    if (ec) return 0;

    // Check if target path starts with base path
    auto base_str = base.lexically_normal().string();
    auto target_str = target.lexically_normal().string();

    if (target_str.rfind(base_str, 0) == 0) {
        return 1; // Safe: target is within base directory
    }
    return 0; // Traversal or outside bounds
}

} // extern "C"
