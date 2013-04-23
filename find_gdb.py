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
def find_gdb(ctx, **kwargs):
    
    ctx.load('hwaf-base', tooldir=_heptooldir)

    # find gdb executable
    gdb = "gdb"
    if getattr(ctx.options, 'with_gdb', None):
        topdir = ctx.options.with_gdb
        topdir = waflib.Utils.subst_vars(topdir, ctx.env)
        gdb = osp.abspath(osp.join(topdir, "bin", "gdb")
            )
        pass
    ctx.find_program(gdb, var='GDB',**kwargs)

    if not ctx.env.GDB_HOME:
        ctx.env.GDB_HOME = osp.dirname(osp.dirname(gdb))
    ctx.env.HWAF_FOUND_GDB = 1
    return

## EOF ##
