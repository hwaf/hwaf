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
    
    if not ctx.env.CC or not ctx.env.CXX:
        msg.fatal('load a C or C++ compiler first')
        pass

    ctx.load('hep-waftools-base', tooldir=_heptooldir)

    kwargs = ctx._findbase_setup(kwargs)
    
    kwargs['mandatory'] = True
    
    # find bzip
    ctx.check(
        features='cxx cxxprogram',
        header_name="bzlib.h",
        lib='bz2',
        uselib_store='bzip',
        **kwargs
        )

    ctx.env.HEPWAF_FOUND_BZIP = 1
    return

## EOF ##
