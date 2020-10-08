import sys
import tempfile
from collections import defaultdict
from datetime import date
from distutils.ccompiler import CCompiler
from distutils.errors import CompileError
from glob import glob
from pathlib import Path

import pybind11
from setuptools import (Extension,
                        find_packages,
                        setup)
from setuptools.command.build_ext import build_ext

import {{project}}


def has_flag(compiler: CCompiler, name: str) -> bool:
    """Detects whether a flag name is supported on the specified compiler."""
    with tempfile.NamedTemporaryFile('w',
                                     suffix='.cpp') as file:
        file.write('int main (int argc, char **argv) { return 0; }')
        try:
            compiler.compile([file.name],
                             extra_postargs=[name])
        except CompileError:
            return False
    return True


def cpp_flag(compiler: CCompiler,
             *,
             min_standard_version: int = 11) -> str:
    """
    Returns the -std=c++[11|...] compiler flag.
    The newer version is preferred when available.
    """
    flags = ['-std=c++{}'.format(version)
             for version in range(min_standard_version,
                                  (date.today().year % 100) + 1, 3)]
    for flag in reversed(flags):
        if has_flag(compiler, flag):
            return flag
    raise RuntimeError('Unsupported compiler: '
                       'at least C++{} support is needed.'
                       .format(min_standard_version))


class BuildExt(build_ext):
    """A custom build extension for adding compiler-specific options."""
    compile_args = defaultdict(list,
                               {'msvc': ['/EHsc'],
                                'unix': []})
    link_args = defaultdict(list,
                            {'msvc': [],
                             'unix': []})
    if sys.platform == 'darwin':
        darwin_args = ['-stdlib=libc++', '-mmacosx-version-min=10.7']
        compile_args['unix'] += darwin_args
        link_args['unix'] += darwin_args

    def build_extensions(self) -> None:
        compiler_type = self.compiler.compiler_type
        compile_args = self.compile_args[compiler_type]
        link_args = self.link_args[compiler_type]
        if compiler_type == 'unix':
            compile_args.append(cpp_flag(self.compiler))
            if has_flag(self.compiler, '-fvisibility=hidden'):
                compile_args.append('-fvisibility=hidden')
        define_macros = [('VERSION_INFO',
                          ('\\"{}\\"' if compiler_type == 'msvc' else '"{}"')
                          .format(self.distribution.get_version()))]
        for extension in self.extensions:
            extension.extra_compile_args = compile_args
            extension.extra_link_args = link_args
            extension.define_macros = define_macros
        super().build_extensions()


project_base_url = 'https://github.com/{{github_login}}/{{project}}/'

setup(name={{project}}.__name__,
      packages=find_packages(exclude=('tests', 'tests.*')),
      version={{project}}.__version__,
      description={{project}}.__doc__,
      long_description=Path('README.md').read_text(encoding='utf-8'),
      long_description_content_type='text/markdown',
      author='{{full_name}}',
      author_email='{{email}}',
      classifiers=[
          '{{license_classifier}}',
{% for minor in range(min_python_version.split(".")[1]|int, (max_python_version.split(".")[1])|int + 1) %}
          'Programming Language :: Python :: 3.{{minor}}',
{% endfor %}
          'Programming Language :: Python :: Implementation :: CPython',
      ],
      license='{{license}}',
      url=project_base_url,
      download_url=project_base_url + 'archive/master.zip',
      python_requires='>={{min_python_version}}',
      install_requires=Path('requirements.txt').read_text(),
      cmdclass={'build_ext': BuildExt},
      ext_modules=[Extension('_' + {{project}}.__name__,
                             glob('src/*.cpp'),
                             include_dirs=[pybind11.get_include(),
                                           pybind11.get_include(True)],
                             language='c++')],
      zip_safe=False)
