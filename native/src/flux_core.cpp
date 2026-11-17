#define FLUX_BUILDING_DLL
#include "flux/flux_core.h"

#include <string_view>
#include <algorithm>
#include <numeric>
#include <span>
#include <vector>

static constexpr const char* NATIVE_VERSION = "FluxKernel-Native-C++20-v0.1.0";

extern "C" {

FLUX_API const char* flux_version(void) {
    return NATIVE_VERSION;
}

FLUX_API int32_t flux_compute(int32_t a, int32_t b) {
    // Basic fast computation kernel with potential overflow protection
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

    // Fast difference calculation
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

} // extern "C"
