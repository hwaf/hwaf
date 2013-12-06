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

def options(ctx):
    ctx.load('hwaf-base', tooldir=_heptooldir)
    ctx.load('find_gdb', tooldir=_heptooldir)
    return

def configure(ctx):
    ctx.load('hwaf-base', tooldir=_heptooldir)
    ctx.load('find_gdb', tooldir=_heptooldir)
    return

@conf
def find_iberty(ctx, **kwargs):
    
    ctx.load('hwaf-base', tooldir=_heptooldir)

    if not ctx.env.HWAF_FOUND_C_COMPILER:
        ctx.fatal('load a C compiler first')
        pass

    if not ctx.env.HWAF_FOUND_GDB:
        # gdb might have installed interesting libs (iberty, bfd)
        ctx.find_gdb(mandatory=False)
        pass
    
    extra_paths = waflib.Utils.to_list(kwargs.get('extra_paths',[]))
    if ctx.env.GDB_HOME:
        gdb = ctx.hwaf_subst_vars('${GDB_HOME}')
        extra_paths.append(gdb)
        pass

    # find libiberty
    ctx.check_with(
        ctx.check,
        "iberty",
        features='c cstlib',
        header_name="libiberty.h",
        stlib='iberty',
        uselib_store='iberty',
        **kwargs
        )
    
    if ctx.env.LIBPATH_iberty and 0:
        ctx.env.STLIBPATH_iberty = ctx.env.LIBPATH_iberty
        ctx.env.STLIB_iberty = ctx.env.LIB_iberty
        ctx.env.LIB_iberty = []
        ctx.env.LIBPATH_iberty = []
        pass

    ctx.env.HWAF_FOUND_IBERTY = 1
    return

## EOF ##
