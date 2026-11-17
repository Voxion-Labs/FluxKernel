#define FLUX_BUILDING_DLL
#include "flux/flux_core.h"

#include <string_view>
#include <string>
#include <algorithm>
#include <numeric>
#include <span>
#include <vector>
#include <filesystem>
#include <system_error>
#include <cctype>

static constexpr const char* NATIVE_VERSION = "FluxKernel-Native-C++20-v0.4.0";

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

    auto base_norm = base.lexically_normal();
    auto target_norm = target.lexically_normal();

    auto rel = target_norm.lexically_relative(base_norm);
    if (rel.empty()) return 0;

    std::string rel_str = rel.string();
    if (rel_str == ".." || rel_str.rfind(".." "/", 0) == 0 || rel_str.rfind("..\\", 0) == 0) {
        return 0;
    }
    if (rel.is_absolute()) {
        return 0;
    }

    return 1;
}

FLUX_API int32_t flux_sandbox_verify_write(const char* base_dir, const char* target_path) {
    if (!flux_sandbox_verify_path(base_dir, target_path)) {
        return 0;
    }

    std::error_code ec;
    fs::path base = fs::weakly_canonical(fs::path(base_dir), ec).lexically_normal();
    fs::path target = fs::weakly_canonical(fs::path(target_path), ec).lexically_normal();
    fs::path rel = target.lexically_relative(base);

    std::string rel_str = rel.generic_string();
    std::string lower_rel = rel_str;
    std::transform(lower_rel.begin(), lower_rel.end(), lower_rel.begin(), [](unsigned char c) {
        return static_cast<char>(std::tolower(c));
    });

    // Block write mutations to protected internal partitions
    if (lower_rel == ".git" || lower_rel.rfind(".git/", 0) == 0 ||
        lower_rel == ".flux_snapshots" || lower_rel.rfind(".flux_snapshots/", 0) == 0 ||
        lower_rel == ".env" || lower_rel.rfind(".env.", 0) == 0) {
        return 0;
    }

    return 1;
}

FLUX_API int32_t flux_security_verify_command(const char* cmd_str) {
    if (!cmd_str) return 0;

    std::string_view sv(cmd_str);
    if (sv.empty()) return 1;

    std::string lower_cmd;
    lower_cmd.reserve(sv.size());
    for (char c : sv) {
        lower_cmd.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(c))));
    }

    static const std::string_view dangerous_patterns[] = {
        "rm -rf /",
        "rm -rf /*",
        "rm -fr /",
        "rmdir /s /q c:\\",
        "rd /s /q c:\\",
        "del /f /s /q c:\\",
        "del /s /q c:\\",
        ":(){ :|:& };:",
        "%0|%0",
        "mkfs",
        "format c:",
        "format d:",
        "diskpart",
        "fdisk",
        "dd if=/dev/zero",
        "dd if=/dev/urandom",
        "chmod -r 777 /",
        "icacls c:\\ /grant",
        "shutdown -s",
        "shutdown /s",
        "init 0",
        "systemctl poweroff",
    };

    for (const auto& pattern : dangerous_patterns) {
        if (lower_cmd.find(pattern) != std::string::npos) {
            return 0; // Rejected dangerous destructive operation
        }
    }

    return 1; // Permitted
}

} // extern "C"
