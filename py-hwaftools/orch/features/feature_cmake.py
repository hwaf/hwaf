#!/usr/bin/env python
'''
This feature is a specific "prepare" feature to set CMake related
configuration items.
'''
from .pfi import feature
from .feature_prepare import generic

requirements = {
    'source-dir': None,
    'source_unpacked': None,
    'unpacked_target': 'CMakeLists.txt',
    'prepare_cmd': 'cmake ../../{source_dir}/{source_unpacked} -DCMAKE_INSTALL_PREFIX={install_dir}',
    'prepare_cmd_options': '',
    'prepare_target': 'CMakeCache.txt',
    'build_dir': None,
    'install_dir': None,
}

@feature('cmake', **requirements)
def feature_cmake(info):
    tags = [x.strip() for x in info.tags.split(',')]
    if 'debug' in tags and 'opt' in tags:
        info.prepare_cmd += ' -DCMAKE_BUILD_TYPE=RelWithDebInfo'
    elif 'debug' in tags:
        info.prepare_cmd += ' -DCMAKE_BUILD_TYPE=Debug'
    elif 'opt' in tags:
        info.prepare_cmd += ' -DCMAKE_BUILD_TYPE=Release'
        
    return generic(info)


