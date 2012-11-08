# -*- python -*-

# waf imports ---
import waflib.Utils
import waflib.Logs as msg
from waflib.Configure import conf

#

def options(opt):

    opt.load('compiler_c compiler_cxx python')
    opt.load('findbase', tooldir="hep-waftools")

    opt.add_option(
        '--with-root',
        default=None,
        help="Look for CERN ROOT System at the given path")
    return

def configure(conf):
    conf.load('compiler_c compiler_cxx python')
    conf.load('findbase platforms', tooldir="hep-waftools")
    return

@conf
def find_cernroot(ctx, **kwargs):
    
    if not ctx.env.CXX:
        msg.fatal('load a C++ compiler first')
        pass


    if not ctx.env.PYTHON:
        msg.fatal('load a python interpreter first')
        pass

    kwargs = ctx._findbase_setup(kwargs)
    
    # find root
    root_cfg = "root-config"
    if ctx.options.with_cern_root_system:
        root_cfg = pjoin(conf.options.with_root, "bin", "root-config")
        pass

    
    kwargs['mandatory'] = True
    
    ctx.check_with(
        ctx.check_cfg,
        path=root_cfg,
        package="",
        uselib_store="ROOT",
        args='--libs --cflags',
        **kwargs)

    ctx.find_program('genmap',      var='GENMAP',     **kwargs)
    ctx.find_program('genreflex',   var='GENREFLEX',  **kwargs)
    ctx.find_program('root',        var='ROOT-EXE',   **kwargs)
    ctx.find_program('root-config', var='ROOT-CONFIG',**kwargs)
    ctx.find_program('rootcint',    var='ROOTCINT',   **kwargs)

    return

## EOF ##
