#include "flux/flux_core.h"
#include <iostream>
#include <cstring>
#include <cassert>
#include <vector>

int main() {
    std::cout << "[FluxKernel Native Test] Starting Phase 3 test suite..." << std::endl;

    // Test 1: Version check
    const char* version = flux_version();
    assert(version != nullptr);
    assert(std::string_view(version).find("FluxKernel-Native-C++20") != std::string_view::npos);
    std::cout << "  ✓ Version check passed: " << version << std::endl;

    // Test 2: Arithmetic compute kernel
    int32_t comp_res = flux_compute(6, 7);
    assert(comp_res == 42);
    std::cout << "  ✓ Compute kernel passed: 6 * 7 = " << comp_res << std::endl;

    // Test 3: Sandbox availability check
    int32_t sandbox_ok = flux_sandbox_available();
    assert(sandbox_ok == 1 || sandbox_ok == 0);
    std::cout << "  ✓ Sandbox capability query passed: " << sandbox_ok << std::endl;

    // Test 4: Diff calculation
    const char* str1 = "hello world";
    const char* str2 = "hello world";
    int64_t diff1 = flux_diff_distance(str1, std::strlen(str1), str2, std::strlen(str2));
    assert(diff1 == 0);

    const char* str3 = "hello earth";
    int64_t diff2 = flux_diff_distance(str1, std::strlen(str1), str3, std::strlen(str3));
    assert(diff2 > 0);
    std::cout << "  ✓ Fast memory diff distance passed: identical=0, mutated=" << diff2 << std::endl;

    // Test 5: Vectorized float dot product
    std::vector<float> vec_a = {1.0f, 2.0f, 3.0f, 4.0f};
    std::vector<float> vec_b = {2.0f, 0.5f, 1.0f, 2.0f};
    // Expected: 1*2 + 2*0.5 + 3*1 + 4*2 = 2 + 1 + 3 + 8 = 14.0f
    float dot_res = flux_fast_vector_dot(vec_a.data(), vec_b.data(), vec_a.size());
    assert(dot_res >= 13.99f && dot_res <= 14.01f);
    std::cout << "  ✓ Vectorized float dot product passed: dot = " << dot_res << std::endl;

    // Test 6: Path verification security check
    int32_t path_safe = flux_sandbox_verify_path(".", "./src");
    assert(path_safe == 1);

    int32_t path_escape = flux_sandbox_verify_path("./src", "./src/../../outside");
    assert(path_escape == 0);
    std::cout << "  ✓ Sandbox path traversal barrier passed: safe=1, escape=0" << std::endl;

    std::cout << "[FluxKernel Native Test] All Phase 3 C++ tests successfully passed!" << std::endl;
    return 0;
}
