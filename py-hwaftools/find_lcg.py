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
    ctx.add_option(
        '--with-lcg',
        default=None,
        help="Look for LCG-heptools at the given path")

    ctx.add_option(
        '--with-lcg-ext-root',
        default=None,
        help="Path to the LCG externals")
    return

def configure(ctx):
    ctx.load('hwaf-base', tooldir=_heptooldir)
    return

@conf
def find_lcg(ctx, **kwargs):
    
    ctx.load('hwaf-base', tooldir=_heptooldir)

    if not ctx.env.HWAF_FOUND_C_COMPILER:
        ctx.fatal('load a C compiler first')
        pass

    if not ctx.env.HWAF_FOUND_CXX_COMPILER:
        ctx.fatal('load a C++ compiler first')
        pass

    lcg_root = ctx.hwaf_subst_vars(ctx.options.with_lcg)
    if not osp.exists(lcg_root):
        ctx.fatal("LCG: no such path [%s]" % lcg_root)
        return

    ctx.msg("LCG-hep-tools", lcg_root)

    lcg_ext_root = ctx.options.with_lcg_ext_root
    ctx.msg("LCG-hep-tools externals", lcg_ext_root)

    
    ctx.env.HWAF_FOUND_LCG = 1
    return

## EOF ##
