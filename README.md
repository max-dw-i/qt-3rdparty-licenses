# qt-3rdparty-licenses

This script finds all the 3rd-party libraries that were used in a Qt build process and export the corresponding 'LICENSE' files into the folder of your choice. To do that, it analyses the 'makefiles' in the build directory. It also needs the file containing the attributes of the Qt 3rd-party libraries. It can be generated with the command:

~~~
qtchooser -run-tool=qtattributionsscanner -qt=5 --output-format 'json' -o 3rdpartylibs.json /path/to/Qt5/sources
~~~

(Qt5 with the **qtattributionsscanner** tool must be installed or built, obviously).

The license files of all 3rd-party libraries can be exported (if needed).

The script has an option to fix the **LicenseFile** and **Path** attributes of the **3rdpartylibs.json** so they point to the correct libraries in the Qt5 source directory (e.g. the **Path** attribute is */home/jack/previous_qt_source/lib*, the Qt5 source directory is */home/alex/new_qt_source* then the new **Path** attribute will be */home/alex/new_qt_source/lib*. It can be useful if we want to generate the **3rdpartylibs.json** once and then use it in different places.

If Qt was built as a 'shadow build', then fixing the paths (-f) will need the Qt source directory as the second argument (since the source and build directories are separate). If Qt was built as a 'non-shadow build', then fixing the paths will need the build directory as the second argument (since the source and build directories are the same thing). Also for a 'non-shadow build' we need to point to a clean Qt source directory (-s) to exclude any premade 'makefiles' from the analysis.

Tested with **Qt5 5.14.2 (qtbase)** on **Linux x64** (**gcc**), **Windows x64** (**MSVC**).

## Usage

~~~
usage: qt-3rdparty-licenses [-h] -o OUTPUT_DIR -a 3RDPARTYLIBS_JSON
                            [-b BUILD_DIR] [-s SRC_DIR]
                            [-f PREV_SRC_DIR SRC_DIR]

optional arguments:
    -h, --help
        show this help message and exit

    -o OUTPUT_DIR, --output OUTPUT_DIR
        directory to export the license files into

    -a 3RDPARTYLIBS_JSON, --attributes 3RDPARTYLIBS_JSON
        path to the generated file with the library attributes

    -b BUILD_DIR, --build BUILD_DIR
        path to the Qt build directory (if not provided, the license files of all 3rd-party Qt libraries will be exported)

    -s SRC_DIR, --source SRC_DIR
        path to the clean Qt source directory (must be provided if a 'non-shadow build' is used)

    -f PREV_SRC_DIR SRC_DIR, --fix PREV_SRC_DIR SRC_DIR
        fix the library paths, provide the previous Qt5 source directory (can be found in '3rdpartylibs.json') and the new Qt5 source directory, for example, -f /home/jack/previous_qt_source /home/alex/new_qt_source; if 'non-shadow build' is used, the new Qt5 source directory is the build directory
~~~

## Examples

- License files export directory - */licenses*
- File with 3rd-party libraries attributes - **3rdpartylibs.json**
- Previous Qt source directory (from **3rdpartylibs.json**) - */prev/Qt/source/dir*
- Qt source directory - */Qt/source/dir*
- Qt build directory - */Qt/build/dir*

1. Qt was built as a 'shadow build' and **3rdpartylibs.json** already has proper paths (point to */Qt/source/dir/...*):

~~~
python licenses.py -o /licenses -a 3rdpartylibs.json -b /Qt/build/dir
~~~

2. Qt was built as a 'shadow build' but we'd like to fix the paths in **3rdpartylibs.json**:

~~~
python licenses.py -o /licenses -a 3rdpartylibs.json -b /Qt/build/dir -f /prev/Qt/source/dir /Qt/source/dir
~~~

3. Qt was built as a 'non-shadow build' and **3rdpartylibs.json** already has proper paths:

~~~
python licenses.py -o /licenses -a 3rdpartylibs.json -b /Qt/build/dir -s /Qt/source/dir
~~~

4. Qt was built as a 'non-shadow build' but we'd like to fix the paths in **3rdpartylibs.json**:

~~~
python licenses.py -o /licenses -a 3rdpartylibs.json -b /Qt/build/dir -s /Qt/source/dir -f /prev/Qt/source/dir /Qt/build/dir
~~~
