# OpenBuudai Qt6

Open Source Oscilloscope Software based on OpenHantek, migrated to **Qt6** with a modern CMake build system.

Originally based on [OpenHantek](https://github.com/OpenHantek/openhantek) by Oliver Haag, extended by doctormord to support Buudai/Rocktech hardware, and updated to Qt6 by [Pejosonic](https://github.com/Pejosonic).

## Supported Hardware

| Device | Status |
|--------|--------|
| SainSmart DDS120 | Supported |
| Buudai / Rocktech BM102 | Supported |
| SainSmart DDS140 | Untested |

## Download

Pre-built Linux binaries are published automatically on every commit:

**[Latest Linux release →](https://github.com/Pejosonic/OpenBuudaiQT6/releases/tag/latest)**

## Qt6 Migration

This fork migrates the original Qt4/Qt5 + qmake project to **Qt6 + CMake**. Key changes:

| Area | Change |
|------|--------|
| Build system | `qmake` → `CMake 3.19+` |
| OpenGL widget | `QGLWidget` → `QOpenGLWidget + QOpenGLFunctions` |
| OpenGL context | Added `QSurfaceFormat` Compatibility Profile for fixed-function pipeline |
| Color helpers | `qglColor / qglClearColor` → `glColor4f / glClearColor` |
| Widget update | Removed `updateGL()` slot → `update()` |
| 2D transforms | `QMatrix / setMatrix` → `QTransform / setTransform` |
| Printer API | `QPrinter::setOrientation / Portrait / Landscape` → `QPageLayout` API |
| Palette | `QPalette::Background` → `QPalette::Window` |
| Library info | `QLibraryInfo::location()` → `QLibraryInfo::path()` |
| Font metrics | `QFontMetrics::size(0, text)` → `boundingRect(text)` |
| WindowFlags | Default arg `= 0` → `= Qt::WindowFlags()` |
| Mouse events | `event->x() / y()` → `event->position().x() / y()` |
| Headers | Added missing explicit Qt includes required by Qt6 |
| Qt modules | Added `Qt6::OpenGLWidgets`, `Qt6::PrintSupport` |

## Build from Source

### Requirements

- CMake 3.19+
- Qt 6.2+ (Core, Gui, Widgets, OpenGL, OpenGLWidgets, PrintSupport)
- libusb-1.0
- fftw3

### Linux (Ubuntu / Debian)

```bash
sudo apt-get install cmake ninja-build \
    qt6-base-dev libqt6opengl6-dev \
    libgl-dev libusb-1.0-0-dev libfftw3-dev

git clone https://github.com/Pejosonic/OpenBuudaiQT6.git
cd OpenBuudaiQT6
cmake -S Source -B build -G Ninja
cmake --build build
```

### macOS (Homebrew)

```bash
brew install cmake ninja qt libusb fftw

git clone https://github.com/Pejosonic/OpenBuudaiQT6.git
cd OpenBuudaiQT6
cmake -S Source -B build -G Ninja -DCMAKE_PREFIX_PATH=$(brew --prefix qt)
cmake --build build
```

### Windows

Install [Qt 6](https://www.qt.io/download) and [CMake](https://cmake.org/download/), then:

```cmd
cmake -S Source -B build -DCMAKE_PREFIX_PATH=C:\Qt\6.x.x\msvc2019_64
cmake --build build --config Release
```

Provide libusb and fftw paths via `-DCMAKE_PREFIX_PATH` or set `LIBUSB_INCLUDE_DIRS` / `FFTW_INCLUDE_DIRS` manually.

## USB Permissions (Linux)

If the status bar shows `Couldn't open device XXX:YYY: Access denied`:

**Quick fix** (per plug-in):
```bash
sudo chmod 666 /dev/bus/usb/XXX/YYY
```

**Permanent fix** via udev rule:
```bash
echo 'SUBSYSTEM=="usb", ATTR{idProduct}=="8102", ATTRS{idVendor}=="8102", MODE="0666"' \
    | sudo tee /etc/udev/rules.d/99-OpenBuudai.rules
sudo udevadm control --reload-rules
```

On Arch Linux (UUCP group):
```bash
echo 'SUBSYSTEM=="usb", ATTR{idProduct}=="8102", ATTRS{idVendor}=="8102", GROUP="uucp"' \
    | sudo tee /etc/udev/rules.d/99-OpenBuudai.rules
sudo gpasswd -a $USER uucp
```

## References

- [Hardware teardown & discussion (360customs)](http://www.360customs.de/en/2014/10/usb-oszilloskop-sainsmart-dds120-2-kanal-20mhz-50msps-buudairocktech-bm102/)
- [EEVblog forum thread](http://www.eevblog.com/forum/testgear/sainsmart-dds120-usb-oscilloscope-%28buudai-bm102%29/)
- [Original OpenHantek](https://github.com/OpenHantek/openhantek)
- [Original OpenBuudai](https://github.com/doctormord/OpenBuudai)
