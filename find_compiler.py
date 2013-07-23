# -*- python -*-

# stdlib imports ---
import os
import os.path as osp

# waf imports ---
import waflib.Utils
import waflib.Logs as msg
from waflib.Configure import conf

#
_heptooldir = osp.dirname(osp.abspath(__file__))

### ---------------------------------------------------------------------------
def options(ctx):
    ctx.load('compiler_c')
    ctx.load('compiler_cxx')
    ctx.load('compiler_fc')

    ctx.add_option(
        '--with-c-compiler',
        default=None,
        help="path to a C compiler")

    ctx.add_option(
        '--with-cxx-compiler',
        default=None,
        help="path to a C++ compiler")

    ctx.add_option(
        '--with-fortran-compiler',
        default=None,
        help="path to a FORTRAN compiler")

    return

### ---------------------------------------------------------------------------
def configure(ctx):
    return

### ---------------------------------------------------------------------------
@conf
def find_c_compiler(ctx, **kwargs):
    # prevent hysteresis
    if ctx.env.HWAF_FOUND_C_COMPILER:
        return

    comp = ctx.env.CFG_COMPILER
    for k,v in {
        'gcc': 'gcc',
        'icc': 'icc',
        'clang': 'clang',
        }.items():
        if comp.startswith(k):
            comp = v
            break
        pass

    if ctx.options.with_c_compiler:
        ctx.env.CC = ctx.options.with_c_compiler
    else:
        ctx.env.CC = os.environ.get('CC', comp)
        pass
    
    ctx.load('c_config')
    ctx.load('compiler_c')

    if ctx.is_opt():
        if ctx.is_windows(): pass
        else: ctx.env.append_unique('CCFLAGS', '-O2')
        pass

    if ctx.is_32b():
        if ctx.is_windows(): pass
        else: ctx.env.append_unique('CCFLAGS', '-m32')
        pass

    if ctx.is_64b():
        if ctx.is_windows(): pass
        else: ctx.env.append_unique('CCFLAGS', '-m64')
        pass

    if ctx.is_darwin():
        # use ELF .so instead of .dyld...
        linkflags = ctx.env.LINKFLAGS_cshlib[:]
        ctx.env.LINKFLAGS_cshlib = [l.replace('-dynamiclib', '-shared')
                                    for l in linkflags]
        ctx.env.cshlib_PATTERN = 'lib%s.so'
        pass
    ctx.env.HWAF_FOUND_C_COMPILER = 1
    return

### ---------------------------------------------------------------------------
@conf
def find_cxx_compiler(ctx, **kwargs):
    # prevent hysteresis
    if ctx.env.HWAF_FOUND_CXX_COMPILER:
        return

    comp = ctx.env.CFG_COMPILER
    for k,v in {
        'gcc': 'g++',
        'g++': 'g++',
        'icc': 'icc',
        'clang': 'clang++',
        }.items():
        if comp.startswith(k):
            comp = v
            break
        pass

    if ctx.options.with_cxx_compiler:
        ctx.env.CXX = ctx.options.with_cxx_compiler
    else:
        ctx.env.CXX = os.environ.get('CXX', comp)
        pass
    
    ctx.load('c_config')
    ctx.load('compiler_cxx')
    if ctx.is_opt():
        if ctx.is_windows(): pass
        else: ctx.env.append_unique('CXXFLAGS', '-O2')
        pass

    if ctx.is_32b():
        if ctx.is_windows(): pass
        else: ctx.env.append_unique('CXXFLAGS', '-m32')
        pass

    if ctx.is_64b():
        if ctx.is_windows(): pass
        else: ctx.env.append_unique('CXXFLAGS', '-m64')
        pass

    if ctx.is_darwin():
        # use ELF .so instead of .dyld...
        linkflags = ctx.env.LINKFLAGS_cxxshlib[:]
        ctx.env.LINKFLAGS_cxxshlib = [l.replace('-dynamiclib', '-shared')
                                      for l in linkflags]
        ctx.env.cxxshlib_PATTERN = 'lib%s.so'
        pass
    ctx.env.HWAF_FOUND_CXX_COMPILER = 1
    return

### ---------------------------------------------------------------------------
@conf
def find_fortran_compiler(ctx, **kwargs):
    # prevent hysteresis
    if ctx.env.HWAF_FOUND_FORTRAN_COMPILER:
        return

    # if ctx.options.with_fortran_compiler:
    #     ctx.env.FC = ctx.options.with_fortran_compiler
    # else:
    #     ctx.env.FC = os.environ.get('FC', comp)
    #     pass
    ctx.load('c_config')
    ctx.load('compiler_fc')

    if ctx.is_32b():
        if ctx.is_windows(): pass
        else: ctx.env.append_unique('FCFLAGS', '-m32')
        pass

    if ctx.is_64b():
        if ctx.is_windows(): pass
        else: ctx.env.append_unique('FCFLAGS', '-m64')
        pass

    if ctx.env.FC_NAME == "GFORTRAN":
        ctx.env['LIB_%s'%"gfortran"] = "gfortran"
        pass
    
    ctx.env.HWAF_FOUND_FORTRAN_COMPILER = 1
    return

## EOF ##

