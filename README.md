# qt-3rdparty-licenses

This script finds all the 3rd-party libraries that were used in a Qt build process and export the corresponding 'LICENSE' files into the folder of your choice. To do that, it analyses the 'makefiles' in the build directory. It also needs the file containing the attributes of the Qt 3rd-party libraries. It can be generated with the command:

~~~
qtchooser -run-tool=qtattributionsscanner -qt=5 --output-format 'json' -o 3rdpartylibs.json /path/to/Qt5/sources
~~~

(Qt5 with the **qtattributionsscanner** tool must be installed or built, obviously).

The license files of all 3rd-party libraries can be exported (if needed).

The script has an option to fix the **LicenseFile** and **Path** attributes of the **3rdpartylibs.json** so they point to the correct libraries in the Qt5 source directory (e.g. the **Path** attribute is */home/jack/previous_qt_source/lib*, the Qt5 source directory is */home/alex/new_qt_source* then the new **Path** attribute will be */home/alex/new_qt_source/lib*. It can be useful if we want to generate the **3rdpartylibs.json** once and then use it in different places.

Tested with **PyQt5 5.14.2** on **Linux x64** (**gcc**), **Windows x64** (**MSVC**).

## Usage

~~~
usage: qt-3rdparty-licenses [-h] -o OUTPUT_DIR -a 3RDPARTYLIBS_JSON
                            [-b BUILD_DIR] [-f PREV_SRC_DIR SRC_DIR]

optional arguments:
    -h, --help

        show this help message and exit,

    -o OUTPUT_DIR, --output OUTPUT_DIR

        directory to export the license files into,

    -a 3RDPARTYLIBS_JSON, --attributes 3RDPARTYLIBS_JSON

        path to the generated file with the library attributes,

    -b BUILD_DIR, --build BUILD_DIR

        path to the Qt build directory (if not provided, the license files of all 3rd-party Qt libraries will be exported),

    -f PREV_SRC_DIR SRC_DIR, --fix PREV_SRC_DIR SRC_DIR

        fix the library paths, provide the previous Qt5 source directory (can be found in '3rdpartylibs.json') and the new Qt5 directory, for example, -f /home/jack/previous_qt_source /home/alex/new_qt_source

The '-o', '-a' options are required, '-b', '-f' - optional
~~~
