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
        '--with-hwaf-toolchain',
        default=None,
        help="path to a complete C/C++/Fortran toolchain")

    ctx.add_option(
        '--with-c-compiler',
        default=None,
        help="path to a C compiler executable")

    ctx.add_option(
        '--with-cxx-compiler',
        default=None,
        help="path to a C++ compiler executable")

    ctx.add_option(
        '--with-fortran-compiler',
        default=None,
        help="path to a FORTRAN compiler executable")

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

    # find CC
    path_list = []
    if getattr(ctx.options, 'with_hwaf_toolchain', None):
        topdir = ctx.options.with_hwaf_toolchain
        topdir = ctx.hwaf_subst_vars(topdir)
        path_list.append(osp.join(topdir, "bin"))
        pass
    elif getattr(ctx.options, 'with_c_compiler', None):
        comp = ctx.options.with_c_compiler
        comp = ctx.hwaf_subst_vars(comp)
        topdir = osp.dirname(comp)
        path_list.append(topdir)
        ctx.env['CC'] = comp
        pass
    else:
        comp = os.environ.get('CC', comp)
        ctx.env['CC'] = comp
        pass
    kwargs['path_list']=path_list
    
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

    # find CXX
    path_list = []
    if getattr(ctx.options, 'with_hwaf_toolchain', None):
        topdir = ctx.options.with_hwaf_toolchain
        topdir = ctx.hwaf_subst_vars(topdir)
        path_list.append(osp.join(topdir, "bin"))
        pass
    elif getattr(ctx.options, 'with_cxx_compiler', None):
        comp = ctx.options.with_cxx_compiler
        comp = ctx.hwaf_subst_vars(comp)
        topdir = osp.dirname(comp)
        path_list.append(topdir)
        ctx.env.CXX = comp
        pass
    else:
        comp = os.environ.get('CXX', comp)
        ctx.env.CXX = comp
        pass
    kwargs['path_list']=path_list
    
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

    comp = ctx.env.CFG_COMPILER
    for k,v in {
        'gcc': 'gfortran',
        'g++': 'gfortran',
        'icc': 'gfortran',
        'clang': 'gfortran',
        }.items():
        if comp.startswith(k):
            comp = v
            break
        pass

    # find FC
    path_list = []
    if getattr(ctx.options, 'with_hwaf_toolchain', None):
        topdir = ctx.options.with_hwaf_toolchain
        topdir = ctx.hwaf_subst_vars(topdir)
        path_list.append(osp.join(topdir, "bin"))
        pass
    elif getattr(ctx.options, 'with_fc_compiler', None):
        comp = ctx.options.with_fc_compiler
        comp = ctx.hwaf_subst_vars(comp)
        topdir = osp.dirname(comp)
        path_list.append(topdir)
        ctx.env.FCC = comp
        pass
    else:
        comp = os.environ.get('FC', comp)
        ctx.env.FCC = comp
        pass
    kwargs['path_list']=path_list
    
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

### ---------------------------------------------------------------------------
@conf
def find_toolchain(ctx, **kw):
    # prevent hysteresis
    if ctx.env.HWAF_FOUND_TOOLCHAIN:
        return

    topdir = getattr(ctx.options, 'with_hwaf_toolchain', None)
    if not topdir:
        topdir = kw.get('path', None)
        pass

    if topdir:

        topdir = ctx.hwaf_subst_vars(topdir)
        if not osp.exists(topdir):
            ctx.fatal("path [%s] does not exist" % topdir)
            pass

        # setup runtime environment
        bindir = osp.join(topdir, 'bin')
        libdir = osp.join(topdir, 'lib')
        if ctx.is_64b() and osp.exists(osp.join(topdir, 'lib64')):
            libdir = osp.join(topdir, 'lib64')
            pass

        os.environ['PATH'] = os.pathsep.join([bindir] + os.environ['PATH'].split(os.pathsep))
        os.environ['LD_LIBRARY_PATH'] = os.pathsep.join([libdir] + os.environ['LD_LIBRARY_PATH'].split(os.pathsep))

        ctx.env.prepend_value('PATH', [bindir])
        ctx.env.prepend_value('LD_LIBRARY_PATH', [libdir])

        pass
    
    # C compiler
    ctx.find_c_compiler(**kw)
    
    # C++ compiler
    ctx.find_cxx_compiler(**kw)
    
    # Fortran compiler
    ctx.find_fortran_compiler(mandatory=False, **kw)
    
    ctx.env.HWAF_FOUND_TOOLCHAIN = 1
    return

## EOF ##

