TEMPLATE = subdirs

# Ensure we build in debug (no stripping, full symbols, zero optimization):
CONFIG += ordered debug
QMAKE_CXXFLAGS_DEBUG += -g -O0

# On Linux, generate a symbol table for backtrace_symbols()
QMAKE_LFLAGS += -rdynamic

# C++ standard
CONFIG += c++14

SUBDIRS += \
    Library \
    GUI \
    Models
