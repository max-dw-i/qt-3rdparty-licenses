'''MIT License

Copyright (c) 2020 Maxim Shpak <maxim.shpak@posteo.uk>

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom
the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
'''


import argparse
import json
import os
import pathlib
import shutil
import sys


def export_used_licenses(export_folder, thirdparty_libs, build_dir,
                         src_dir=None):
    '''Exporting the licenses of the used Qt 3rd-party libraries to
    the :export_folder: folder

    :param export_folder:   directory where to put the license files in,
    :param thirdparty_libs: list containing the Qt 3rd-party libraries with its
                            attributes (List[Dict[Attribute, Value]]),
    :param build_dir:       Qt build directory (need because 'Makefile's are
                            analysed to find out what 3rd-party libraries are
                            used in the Qt build),
    :param src_dir:         separate and clean Qt source directory (optional,
                            if a 'non-shadow build' is used, need to exclude
                            any premade 'Makefile's from the analysis; if a
                            'shadow built' is used, there'll not be any in
                            the build directory)
    '''

    print('Exporting the licenses of the used Qt 3rd-party libraries...')

    export_folder = pathlib.Path(export_folder)

    libs = libraries_factory(thirdparty_libs)

    for mf_path in Makefile.search(build_dir, src_dir=src_dir):
        mf = Makefile(mf_path)
        for lib in libs.copy():
            if lib.used(mf):
                new_license_dir = export_folder / lib.id()
                lib.export_license_file(new_license_dir)
                libs.remove(lib)


def libraries_factory(thirdparty_libs):
    '''Return a set of 'library' objects based on the attributes from
    :thirdparty_libs:

    :param thirdparty_libs: list containing the Qt 3rd-party libraries with its
                            attributes (List[Dict[Attribute, Value]]),
    :return: Set[Union[Library, WebgradientsLib]]
    '''

    libs = set()
    for lib_attrs in thirdparty_libs:
        id = lib_attrs['Id']
        if id == 'webgradients':
            lib = WebgradientsLib(lib_attrs)
        else:
            lib = Library(lib_attrs)

        libs.add(lib)
    return libs


def export_all_licenses(export_folder, thirdparty_libs):
    '''Exporting the licenses of all Qt 3rd-party libraries to
    the :export_folder: folder

    :param export_folder:   directory where to put the license files in,
    :param thirdparty_libs: list containing the Qt 3rd-party libraries with its
                            attributes (List[Dict[Attribute, Value]])
    '''

    print('Exporting the licenses of all Qt 3rd-party libraries...')

    export_folder = pathlib.Path(export_folder)

    libs = {Library(lib_attrs) for lib_attrs in thirdparty_libs}
    for lib in libs:
        new_license_dir = export_folder / lib.id()
        lib.export_license_file(new_license_dir)


def fix_3rdpartylib_paths(thirdparty_libs, prev_src_dir, src_dir):
    '''Change the 'LicenseFile' and 'Path' attributes so they point to the
    correct libraries in :src_dir: (e.g. the 'Path' attribute is
    '/home/jack/prev_qt_source/lib', :src_dir: is '/home/alex/new_qt_source'
    and :prev_src_dir: is '/home/jack/prev_qt_source', then the new 'Path' will
    be '/home/alex/new_qt_source/lib'. It can be useful if we want to
    generate the file with 3rd-party library attributes once and then use
    it in different places

    :param thirdparty_libs: list containing the Qt 3rd-party libraries with its
                            attributes (List[Dict[Attribute, Value]]),
    :param prev_src_folder: previous Qt source folder
                            (e.g. 'prev_qt_source'),
    :param src_dir:         Qt source directory
                            (e.g. '/home/alex/new_qt_source')
    '''

    src_dir = pathlib.Path(src_dir)
    prev_src_dir = pathlib.Path(prev_src_dir)

    for lib in thirdparty_libs:
        for path_attr in ['LicenseFile', 'Path']:
            path = lib[path_attr]
            if not path:
                continue

            path_parts = pathlib.Path(path).parts
            prev_src_folder_pos = path_parts.index(prev_src_dir.name)
            same_parts = path_parts[prev_src_folder_pos+1:]
            lib[path_attr] = str(src_dir.joinpath(*same_parts))


class Library:
    '''Represent a 3rd-party library used by Qt

    :param lib_data: dictionary with 3rd-party library attributes (from
                     '3rdpartylibs.json' file)
    '''

    def __init__(self, lib_data):
        self._data = lib_data
        self._signatures = []

    def used(self, makefile):
        '''Return True if any of the library files is found in :makefile:,
        False - otherwise

        :param makefile: Makefile object
        '''

        for sig in self.signatures:
            if makefile.has_path(sig):
                return True
        return False

    @property
    def signatures(self):
        '''Return the library file paths that used to find out if the lib is
        used in a Qt build. If the lib does not have information about
        the library files but only directory, the path to the directory will
        be returned, for example, '.../3rdparty/pcre2/' (with a trailing slash)
        '''

        sigs = self._signatures
        if sigs:
            return sigs

        lib_path, lib_filenames = pathlib.Path(self.path()), self.files()
        if lib_filenames: # e.g. 'linuxperf'
            lib_filepaths = [str(lib_path / name) for name in lib_filenames]
        elif lib_path.suffix: # e.g. 'grayraster'
            lib_filepaths = [lib_path]
        else: # e.g. 'angle'
            suffixes = (
                '.h', '.hh',
                '.c', '.cpp', '.cc',
                '.jar', # 'gradle', NEED TO BE TESTED (ANDROID)
                '.S', # 'pixman', NEED TO BE TESTED (ARM NEON)
                '.ttf' # fonts for WASM, NEED TO BE TESTED
            )
            lib_filepaths = [filepath for filepath in lib_path.rglob('*')
                             if filepath.suffix in suffixes]

        self._signatures = lib_filepaths
        return lib_filepaths

    def files(self):
        '''Return the library files (from the "Files" attribute). If there is
        none, an empty list is returned
        '''

        files = self._data['Files'].split(' ')
        files = [name.rstrip(',') for name in files]
        return files

    def path(self):
        '''Return the library path (from the "Path" attribute)'''

        return self._data['Path']

    def license_file(self):
        '''Return the path to the license file (from the "LicenseFile"
        attribute)
        '''

        return self._data['LicenseFile']

    def export_license_file(self, export_folder):
        '''Copy the license file into :export_folder:

        :param export_folder: folder to copy the license file into
        '''

        if not export_folder.exists():
            export_folder.mkdir(parents=True)

        license_file_path = self.license_file()
        if license_file_path:
            name = pathlib.Path(license_file_path).name
            new_path = export_folder / name
            shutil.copyfile(license_file_path, new_path)
        else:
            # If no license file in the attributes, it's 'Public Domain'
            self._public_domain(export_folder)

    def _public_domain(self, export_folder):
        license_file_path = export_folder / 'Public Domain'
        with open(license_file_path, 'w') as f:
            f.write(self._data['Copyright'])

    def id(self):
        '''Return the library identificator (unique, from the "Id"
        attribute)
        '''

        return self._data['Id']

    def __eq__(self, l):
        if not isinstance(l, Library):
            return NotImplemented
        return self.id() == l.id()

    def __hash__(self):
        return hash(self.id())


class WebgradientsLib(Library):
    '''Represent the 'webgradients' 3rd-party library'''

    @property
    def signatures(self):
        '''Return the 'webgradients.binaryjson' path'''

        file_path = super().signatures[0]
        parts = file_path.split('.')
        # Not '.css' but premade '.binaryjson' is used in compilation
        parts[-1] = 'binaryjson'
        return ['.'.join(parts)]


class Makefile:
    '''Represent a Makefile used in a Qt build process

    :param file_path: path to the Makefile
    '''

    def __init__(self, file_path):
        self.file_path = pathlib.Path(file_path)

        with open(file_path, 'r') as f:
            self._data = f.read()

    def has_path(self, path):
        '''Check if the Makefile uses :path: in the Qt build process

        :param path: path to some file,
        :return: True - the path has been found, False - otherwise
        '''

        separators = {' ', '\n', '\t'}
        data = self._data
        search_area_start = data.find('####### Compile')
        if search_area_start == -1:
            return False

        search_area_end = data.find('####### Install')

        # Makefiles generated by qmake do not use implicit rules, wildcards (as
        # far as I know, only explicit rules) so it must be sufficient just to
        # search for library files

        path = pathlib.Path(path)
        name = str(path.name)
        i = data.find(name, search_area_start, search_area_end)
        while i != -1:
            start, end = i, i

            while data[start] not in separators:
                start -= 1

            while data[end] not in separators:
                end += 1

            contender = self._sanitise(data[start+1:end])
            if contender.startswith(str(path)):
                return True

            i = data.find(name, end+1, search_area_end)

        return False

    def _sanitise(self, s):
        if s[-1] == ':':
            return ''

        for prefix in ('-I', '$(INSTALL_ROOT)'):
            if s.startswith(prefix):
                s = s[len(prefix):]

        cwd = pathlib.Path.cwd()
        os.chdir(self.file_path.parent)
        path = pathlib.Path(s).resolve()
        os.chdir(cwd)
        return str(path)

    @staticmethod
    def search(build_dir, src_dir=None):
        '''Search 'Makefiles' in a Qt build directory

        :param build_dir:   Qt build directory,
        :param src_dir:     separate and clean Qt source directory (optional,
                            if need to exclude any premade 'Makefile's),
        :return:            list with the paths of the found 'Makefile's
        '''

        makefile_name = 'Makefile' # Linux, gcc

        # Exclude the premade 'Makefile's
        exclude_mfs = []
        if src_dir is not None:
            src_dir = pathlib.Path(src_dir)
            for mf_path in src_dir.rglob(makefile_name):
                path_tail = str(mf_path.relative_to(src_dir))
                exclude_mfs.append(path_tail)

        exclude_mfs = tuple(exclude_mfs)

        if sys.platform.startswith('win'):
            makefile_name = 'Makefile*Release' # Win, msvc

        build_dir = pathlib.Path(build_dir)
        makefiles = [mf_path for mf_path in build_dir.rglob(makefile_name)
                     if not str(mf_path).endswith(exclude_mfs)]
        return makefiles


if __name__ == '__main__':

    NAME = 'qt-3rdparty-licenses'
    DESCRIPTION = (
        "This script finds all the 3rd-party libraries that were used in a Qt "
        "build process and export the corresponding 'LICENSE' files into the "
        "folder of your choice. To do that, it analyses the makefiles in the "
        "build directory ('Makefile' on Linux, gcc; 'Makefile.Release' on "
        "Windows, MSVC). It also needs the file containing the attributes of "
        "the Qt 3rd-party libraries. It can be generated with the command:\n\n"
        ">> 'qtchooser -run-tool=qtattributionsscanner -qt=5 --output-format "
        "'json' -o 3rdpartylibs.json /path/to/Qt5/sources'\n\n"
        "(Qt5 with the 'qtattributionsscanner' tool must be installed or "
        "built, obviously).\n"
        "The license files of all 3rd-party libraries can be exported (if "
        "needed).\n"
        "The script has an option to fix the 'LicenseFile' and 'Path' "
        "attributes of the '3rdpartylibs.json' so they point to the correct "
        "libraries in the Qt5 source directory (e.g. the 'Path' attribute is "
        "'/home/jack/previous_qt_source/lib', the Qt5 source directory is "
        "'/home/alex/new_qt_source' then the new 'Path' attribute will be "
        "'/home/alex/new_qt_source/lib'. It can be useful if we want to "
        "generate the '3rdpartylibs.json' once and then use it in "
        "different places.\n"
        "If Qt was built as a 'shadow build', then fixing the paths (-f) will "
        "need the Qt source directory as the second argument (since the "
        "source and build directories are separate). If Qt was built as a "
        "'non-shadow build', then fixing the paths will need the build "
        "directory as the second argument (since the source and build "
        "directories are the same thing). Also for a 'non-shadow build' we "
        "need to point to a clean Qt source directory (-s) to exclude any "
        "premade 'Makefile's from the analysis.\n\n"
        "Examples:\n\n"
        "- License files export directory - '/licenses'\n"
        "- File with 3rd-party libraries attributes - '3rdpartylibs.json'\n"
        "- Previous Qt source directory (from '3rdpartylibs.json') - "
        "'/prev/Qt/source/dir'\n"
        "- Qt source directory - '/Qt/source/dir'\n"
        "- Qt build directory - '/Qt/build/dir'\n\n"
        "1. Qt was built as a 'shadow build' and '3rdpartylibs.json' already "
        "has proper paths (point to '/Qt/source/dir/...'):\n\n"
        ">> python licenses.py -o /licenses -a 3rdpartylibs.json -b "
        "/Qt/build/dir\n\n"
        "2. Qt was built as a 'shadow build' but we'd like to fix the paths "
        "in '3rdpartylibs.json':\n\n"
        ">> python licenses.py -o /licenses -a 3rdpartylibs.json -b "
        "/Qt/build/dir -f /prev/Qt/source/dir /Qt/source/dir\n\n"
        "3. Qt was built as a 'non-shadow build' and '3rdpartylibs.json' "
        "already has proper paths:\n\n"
        ">> python licenses.py -o /licenses -a 3rdpartylibs.json -b "
        "/Qt/build/dir -s /Qt/source/dir\n\n"
        "4. Qt was built as a 'non-shadow build' but we'd like to fix the "
        "paths in '3rdpartylibs.json':\n\n"
        ">> python licenses.py -o /licenses -a 3rdpartylibs.json -b "
        "/Qt/build/dir -s /Qt/source/dir -f /prev/Qt/source/dir /Qt/build/dir"
    )

    parser = argparse.ArgumentParser(
        prog=NAME,
        description=DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '-o',
        '--output',
        metavar='OUTPUT_DIR',
        help='directory to export the license files into',
        required=True,
    )
    parser.add_argument(
        '-a',
        '--attributes',
        metavar='3RDPARTYLIBS_JSON',
        help='path to the generated file with the library attributes',
        required=True,
    )
    parser.add_argument(
        '-b',
        '--build',
        metavar='BUILD_DIR',
        help=('path to the Qt build directory (if not provided, the license '
              'files of all 3rd-party Qt libraries will be exported)'),
    )
    parser.add_argument(
        '-s',
        '--source',
        metavar='SRC_DIR',
        help=("path to the clean Qt source directory (must be provided if "
              "a 'non-shadow build' is used)"),
    )
    parser.add_argument(
        '-f',
        '--fix',
        nargs=2,
        metavar=('PREV_SRC_DIR', 'SRC_DIR'),
        help=("fix the library paths, provide the previous Qt5 source "
              "directory (can be found in '3rdpartylibs.json') and the new "
              "Qt5 source directory, for example, "
              "-f /home/jack/previous_qt_source /home/alex/new_qt_source; "
              "if 'non-shadow build' is used, the new Qt5 source directory "
              "is the build directory"),
    )
    args = parser.parse_args()

    with open(args.attributes, 'r') as f:
        thirdparty_libs = json.load(f)

    fix = args.fix
    if fix is not None:
        fix_3rdpartylib_paths(thirdparty_libs, fix[0], fix[1])

    export_dir = args.output
    build_dir = args.build
    if build_dir is None:
        export_all_licenses(export_dir, thirdparty_libs)
    else:
        src_dir = args.source
        export_used_licenses(export_dir, thirdparty_libs, build_dir, src_dir)
