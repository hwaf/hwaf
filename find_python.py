# -*- python -*-

# stdlib imports ---
import os
import os.path as osp

# waf imports ---
import waflib.Utils
import waflib.Logs as msg
from waflib.Configure import conf

#

def options(ctx):

    ctx.load('compiler_c compiler_cxx python')
    ctx.load('findbase', tooldir="hep-waftools")

    ctx.add_option(
        '--with-root-sys',
        default=None,
        help="Look for CERN ROOT System at the given path")
    return

def configure(ctx):
    ctx.load('compiler_c compiler_cxx python')
    ctx.load('findbase platforms', tooldir="hep-waftools")
    return

@conf
def find_cernroot(ctx, **kwargs):
    
    ctx.load('findbase platforms', tooldir="hep-waftools")

    if not ctx.env.CXX:
        msg.fatal('load a C++ compiler first')
        pass

