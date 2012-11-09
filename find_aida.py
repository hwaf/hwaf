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

    opt.load('findbase', tooldir=_heptooldir)

    opt.add_option(
        '--with-aida',
        default=None,
        help="Look for AIDA at the given path")
    return

def configure(conf):
    conf.load('findbase platforms', tooldir=_heptooldir)
    return

@conf
def find_aida(ctx, **kwargs):
    
    if not ctx.env.CXX:
        msg.fatal('load a C++ compiler first')
        pass


    kwargs = ctx._findbase_setup(kwargs)
    
    kwargs['mandatory'] = True
    ctx.check_with(
        ctx.check,
        "aida",
        features='cxx cxxprogram',
        header_name="AIDA/AIDA.h",
        uselib_store='AIDA',
        **kwargs
        )
    
    ctx.env.HEPWAF_FOUND_AIDA = 1
    return

## EOF ##
