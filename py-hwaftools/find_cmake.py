# -*- python -*-

# stdlib imports ---
import os
import os.path as osp
import textwrap

# waf imports ---
import waflib.Utils
import waflib.Logs as msg
from waflib.Configure import conf

#
_heptooldir = osp.dirname(osp.abspath(__file__))

def options(opt):

    opt.load('hwaf-base', tooldir=_heptooldir)

    opt.add_option(
        '--with-cmake',
        default=None,
        help="Look for CMake at the given path")
    return

def configure(conf):
    conf.load('hwaf-base', tooldir=_heptooldir)
    return

@conf
def find_cmake(ctx, **kwargs):
    
    if not ctx.env.HWAF_FOUND_C_COMPILER:
        ctx.fatal('load a C compiler first')
        pass

    if not ctx.env.HWAF_FOUND_CXX_COMPILER:
        ctx.fatal('load a C++ compiler first')
        pass


    path_list = waflib.Utils.to_list(kwargs.get('path_list', []))
    if getattr(ctx.options, 'with_cmake', None):
        topdir = ctx.options.with_cmake
        topdir = ctx.hwaf_subst_vars(topdir)
        path_list.append(osp.join(topdir, "bin"))
        pass
    kwargs['path_list'] = path_list
    
    ctx.find_program(
        "cmake",
        var="CMAKE",
        **kwargs)

    kwargs['mandatory'] = False
    ctx.find_program(
        "ccmake",
        var="CCMAKE",
        **kwargs)
    
    ctx.find_program(
        "cpack",
        var="CPACK",
        **kwargs)
    
    ctx.find_program(
        "ctest",
        var="CTEST",
        **kwargs)

    version="N/A"
    cmd = [ctx.env.CMAKE, "--version"]
    lines=ctx.cmd_and_log(cmd).splitlines()
    for l in lines:
        l = l.lower()
        if "version" in l:
            version=l[l.find("version")+len("version"):].strip()
            break
        pass
    ctx.start_msg("CMake version")
    ctx.end_msg(version)

    ctx.hwaf_declare_runtime_env('CMAKE')

    ctx.env.CMAKE_HOME = osp.dirname(osp.dirname(ctx.env.CMAKE))
    ctx.env.CMAKE_VERSION = version
    ctx.env.HWAF_FOUND_CMAKE = 1
    return

## EOF ##
