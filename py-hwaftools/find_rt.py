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
    return

def configure(ctx):
    ctx.load('hwaf-base', tooldir=_heptooldir)
    return

@conf
def find_rt(ctx, **kwargs):
    
    ctx.load('hwaf-base', tooldir=_heptooldir)

    if not ctx.env.HWAF_FOUND_C_COMPILER:
        ctx.fatal('load a C compiler first')
        pass

    if not ctx.is_linux():
        return
    
    # find rt
    ctx.check_with(
        ctx.check,
        "rt",
        features='c cprogram',
        lib='rt',
        uselib_store='rt',
        **kwargs
        )

    ctx.env.HWAF_FOUND_RT = 1
    return

## EOF ##
