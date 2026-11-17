#ifndef FLUX_CORE_H
#define FLUX_CORE_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

#if defined(_WIN32) || defined(__CYGWIN__)
  #ifdef FLUX_BUILDING_DLL
    #define FLUX_API __declspec(dllexport)
  #else
    #define FLUX_API __declspec(dllimport)
  #endif
#else
  #if defined(__GNUC__) && __GNUC__ >= 4
    #define FLUX_API __attribute__((visibility("default")))
  #else
    #define FLUX_API
  #endif
#endif

/**
 * @brief Returns the version identifier of the native C++ engine.
 */
FLUX_API const char* flux_version(void);

/**
 * @brief High-speed integer arithmetic computation kernel.
 */
FLUX_API int32_t flux_compute(int32_t a, int32_t b);

/**
 * @brief Checks if native OS sandbox isolation primitives are available.
 * @return 1 if available, 0 otherwise.
 */
FLUX_API int32_t flux_sandbox_available(void);

/**
 * @brief Computes fast byte-level similarity distance between two memory buffers.
 */
FLUX_API int64_t flux_diff_distance(const char* a, size_t len_a, const char* b, size_t len_b);

#ifdef __cplusplus
}
#endif

#endif // FLUX_CORE_H
