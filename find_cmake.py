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

def options(opt):

    opt.load('hep-waftools-base', tooldir=_heptooldir)

    opt.add_option(
        '--with-cmake',
        default=None,
        help="Look for CMake at the given path")
    return

def configure(conf):
    conf.load('hep-waftools-base', tooldir=_heptooldir)
    return

@conf
def find_cmake(ctx, **kwargs):
    
    if not ctx.env.CXX:
        msg.fatal('load a C++ compiler first')
        pass


    path_list = []
    if ctx.options.with_cmake:
        path_list.append(
            osp.join(ctx.options.with_cmake, "bin")
            )
        pass

    ctx.find_program(
        "cmake",
        var="CMAKE",
        path_list=path_list,
        **kwargs)
    
    ctx.find_program(
        "ccmake",
        var="CCMAKE",
        path_list=path_list,
        **kwargs)
    
    ctx.find_program(
        "cpack",
        var="CPACK",
        path_list=path_list,
        **kwargs)
    
    ctx.find_program(
        "ctest",
        var="CTEST",
        path_list=path_list,
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

    ctx.env.HEPWAF_FOUND_CMAKE = 1
    return

## EOF ##
