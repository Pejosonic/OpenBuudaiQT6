cmake_minimum_required(VERSION 3.19)
project(OpenBuudai VERSION 0.3.1 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)

find_package(Qt6 REQUIRED COMPONENTS Core Gui Widgets OpenGL OpenGLWidgets PrintSupport LinguistTools)

find_package(PkgConfig QUIET)
if(PkgConfig_FOUND)
    pkg_check_modules(LIBUSB libusb-1.0)
    pkg_check_modules(FFTW fftw3)
endif()

# Fallback: find via find_library (e.g. Homebrew on macOS)
if(NOT LIBUSB_FOUND)
    find_path(LIBUSB_INCLUDE_DIRS NAMES libusb.h libusb-1.0/libusb.h
        PATHS /opt/homebrew/include /usr/local/include /usr/include)
    find_library(LIBUSB_LIBRARIES NAMES usb-1.0 usb
        PATHS /opt/homebrew/lib /usr/local/lib /usr/lib)
    if(LIBUSB_LIBRARIES)
        set(LIBUSB_FOUND TRUE)
        message(STATUS "Found libusb: ${LIBUSB_LIBRARIES}")
    else()
        message(WARNING "libusb-1.0 not found — install it (e.g. brew install libusb)")
    endif()
endif()

if(NOT FFTW_FOUND)
    find_path(FFTW_INCLUDE_DIRS NAMES fftw3.h
        PATHS /opt/homebrew/include /usr/local/include /usr/include)
    find_library(FFTW_LIBRARIES NAMES fftw3
        PATHS /opt/homebrew/lib /usr/local/lib /usr/lib)
    if(FFTW_LIBRARIES)
        set(FFTW_FOUND TRUE)
        message(STATUS "Found fftw3: ${FFTW_LIBRARIES}")
    else()
        message(WARNING "fftw3 not found — install it (e.g. brew install fftw)")
    endif()
endif()

set(SOURCES
    src/colorbox.cpp
    src/configdialog.cpp
    src/configpages.cpp
    src/dataanalyzer.cpp
    src/dockwindows.cpp
    src/dsocontrol.cpp
    src/dsowidget.cpp
    src/exporter.cpp
    src/glgenerator.cpp
    src/glscope.cpp
    src/helper.cpp
    src/levelslider.cpp
    src/main.cpp
    src/openhantek.cpp
    src/settings.cpp
    src/hantek/hantek_control.cpp
    src/hantek/hantek_device.cpp
    src/hantek/hantek_types.cpp
    src/buudai/buudai_control.cpp
    src/buudai/buudai_device.cpp
    src/buudai/buudai_types.cpp
    src/dso.cpp
)

qt6_add_translation(QM_FILES translations/openhantek_de.ts)

add_executable(OpenBuudai
    ${SOURCES}
    res/application.qrc
    res/configdialog.qrc
    ${QM_FILES}
)

target_include_directories(OpenBuudai PRIVATE src)

if(LIBUSB_FOUND)
    target_include_directories(OpenBuudai PRIVATE ${LIBUSB_INCLUDE_DIRS})
    target_link_libraries(OpenBuudai PRIVATE ${LIBUSB_LIBRARIES})
endif()

if(FFTW_FOUND)
    target_include_directories(OpenBuudai PRIVATE ${FFTW_INCLUDE_DIRS})
    target_link_libraries(OpenBuudai PRIVATE ${FFTW_LIBRARIES})
endif()

target_link_libraries(OpenBuudai PRIVATE
    Qt6::Core
    Qt6::Gui
    Qt6::Widgets
    Qt6::OpenGL
    Qt6::OpenGLWidgets
    Qt6::PrintSupport
)

target_compile_definitions(OpenBuudai PRIVATE
    LIBUSB_VERSION=1
    VERSION="${PROJECT_VERSION}"
)

if(UNIX AND NOT APPLE)
    set(TRANSLATIONS_INSTALL_PATH "${CMAKE_INSTALL_PREFIX}/share/apps/openhantek/translations")
    target_compile_definitions(OpenBuudai PRIVATE
        OS_UNIX
        "QMAKE_TRANSLATIONS_PATH=\"${TRANSLATIONS_INSTALL_PATH}\""
    )
    install(TARGETS OpenBuudai DESTINATION bin)
    install(FILES ${QM_FILES} DESTINATION ${TRANSLATIONS_INSTALL_PATH})
elseif(APPLE)
    target_compile_definitions(OpenBuudai PRIVATE
        OS_DARWIN
        "QMAKE_TRANSLATIONS_PATH=\"Contents/Resources/translations\""
    )
    set_target_properties(OpenBuudai PROPERTIES
        MACOSX_BUNDLE TRUE
        MACOSX_BUNDLE_ICON_FILE openhantek.icns
    )
    install(FILES res/images/openhantek.icns
        DESTINATION OpenBuudai.app/Contents/Resources)
    install(FILES ${QM_FILES}
        DESTINATION OpenBuudai.app/Contents/Resources/translations)
elseif(WIN32)
    target_compile_definitions(OpenBuudai PRIVATE
        OS_WINDOWS
        "QMAKE_TRANSLATIONS_PATH=\"translations\""
    )
    install(TARGETS OpenBuudai DESTINATION .)
    install(FILES ${QM_FILES} DESTINATION translations)
endif()
