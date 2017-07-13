cmake_minimum_required(VERSION 3.0)


PROJECT( GUI )

set(CMAKE_BUILD_TYPE RELEASE)

if (UNIX)
    set(CMAKE_CXX_FLAGS "-std=c++14 -Wall")
else ()
    set(CMAKE_CXX_FLAGS "/c /Zi /GS- /GL /W3 /Gy /Gm- /Ox /EHsc /W3 /O2 /MD")
    set(CMAKE_EXE_LINKER_FLAGS "/LTCG /DEBUG")
endif ()

find_package(PythonLibs 2.7 REQUIRED)

include_directories(
${PYTHON_INCLUDE_DIRS}
)



add_executable(GUI GUI.c)

target_link_libraries(GUI
${PYTHON_LIBRARIES}
)

