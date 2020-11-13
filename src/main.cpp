#include <pybind11/pybind11.h>

namespace py = pybind11;

#define MODULE_NAME _{{project}}
#define C_STR_HELPER(a) #a
#define C_STR(a) C_STR_HELPER(a)
#ifndef VERSION_INFO
#define VERSION_INFO "dev"
#endif

PYBIND11_MODULE(MODULE_NAME, m) {
  m.doc() = R"pbdoc({{description}})pbdoc";
  m.attr("__version__") = C_STR(VERSION_INFO);
}
