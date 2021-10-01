import platform
from pathlib import Path

from setuptools import (find_packages,
                        setup)

import {{project}}

project_base_url = 'https://github.com/{{github_login}}/{{project}}/'


def read_file(path_string: str) -> str:
    return Path(path_string).read_text(encoding='utf-8')


parameters = dict(
        name={{project}}.__name__,
        packages=find_packages(exclude=('tests', 'tests.*')),
        version={{project}}.__version__,
        description={{project}}.__doc__,
        long_description=read_file('README.md'),
        long_description_content_type='text/markdown',
        author='{{full_name}}',
        author_email='{{email}}',
        license='{{license}}',
        classifiers=[
            '{{license_classifier}}',
{% for minor in range(min_python_version.split(".")[1] | int, (max_python_version.split(".")[1]) | int + 1) %}
            'Programming Language :: Python :: 3.{{minor}}',
{% endfor %}
            'Programming Language :: Python :: Implementation :: CPython',
            'Programming Language :: Python :: Implementation :: PyPy',
        ],
        url=project_base_url,
        download_url=project_base_url + 'archive/master.zip',
        python_requires='>={{min_python_version}}',
        setup_requires=read_file('requirements-setup.txt'))
if platform.python_implementation() == 'CPython':
    import sys
    import tempfile
    from collections import defaultdict
    from datetime import date
    from distutils.ccompiler import CCompiler
    from distutils.errors import CompileError
    from glob import glob
    from typing import Any

    from setuptools import (Command,
                            Extension)
    from setuptools.command.build_ext import build_ext
    from setuptools.command.develop import develop


    def has_flag(compiler: CCompiler, name: str) -> bool:
        """
        Detects whether a flag name is supported on the specified compiler.
        """
        with tempfile.NamedTemporaryFile('w',
                                         suffix='.cpp') as file:
            file.write('int main(void) { return 0; }')
            try:
                compiler.compile([file.name],
                                 extra_postargs=[name])
            except CompileError:
                return False
        return True


    def cpp_flag(compiler: CCompiler) -> str:
        """
        Returns the -std=c++[11|...] compiler flag.
        The newer version is preferred when available.
        """
        flags = ['-std=c++{}'.format(str(year)[2:])
                 for year in range(2011, date.today().year + 1, 3)]
        for flag in reversed(flags):
            if has_flag(compiler, flag):
                return flag
        raise RuntimeError('Unsupported compiler: '
                           'at least C++11 support is needed.')


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
            define_macros = [('VERSION_INFO', self.distribution.get_version())]
            for extension in self.extensions:
                extension.extra_compile_args = compile_args
                extension.extra_link_args = link_args
                extension.define_macros = define_macros
            super().build_extensions()


    class Develop(develop):
        def reinitialize_command(self,
                                 name: str,
                                 reinit_subcommands: int = 0,
                                 **kwargs: Any) -> Command:
            if name == build_ext.__name__:
                kwargs.setdefault('debug', 1)
            result = super().reinitialize_command(name, reinit_subcommands,
                                                  **kwargs)
            if name == build_ext.__name__:
                result.ensure_finalized()
                for extension in result.extensions:
                    extension.undef_macros.append('NDEBUG')
            return result


    class LazyPybindInclude:
        def __str__(self) -> str:
            import pybind11
            return pybind11.get_include()


    parameters.update(
            cmdclass={build_ext.__name__: BuildExt,
                      develop.__name__: Develop},
            ext_modules=[Extension('_' + {{project}}.__name__,
                                   glob('src/*.cpp'),
                                   include_dirs=[LazyPybindInclude()],
                                   language='c++')],
            zip_safe=False)
setup(**parameters)
