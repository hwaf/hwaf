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
    ctx.load('hep-waftools-base', tooldir=_heptooldir)
    return

def configure(ctx):
    ctx.load('hep-waftools-base', tooldir=_heptooldir)
    return

@conf
def find_bzip(ctx, **kwargs):
    
    ctx.load('hep-waftools-base', tooldir=_heptooldir)
    if not ctx.env.HEPWAF_FOUND_C_COMPILER:
        ctx.fatal('load a C compiler first')
        pass

    if not ctx.env.HEPWAF_FOUND_CXX_COMPILER:
        ctx.fatal('load a C++ compiler first')
        pass

    # find bzip
    ctx.check_with(
        ctx.check,
        "bzip",
        features='cxx cxxprogram',
        header_name="bzlib.h",
        lib='bz2',
        uselib_store='bzip',
        **kwargs
        )

    ctx.env.HEPWAF_FOUND_BZIP = 1
    return

## EOF ##
