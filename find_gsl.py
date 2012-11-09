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
        '--with-gsl',
        default=None,
        help="Look for GSL at the given path")
    return

def configure(conf):
    conf.load('hep-waftools-base', tooldir=_heptooldir)
    return

@conf
def find_gsl(ctx, **kwargs):
    
    if not ctx.env.CXX:
        msg.fatal('load a C++ compiler first')
        pass


    kwargs = ctx._findbase_setup(kwargs)
    
    kwargs['mandatory'] = kwargs.get('mandatory', False)
    ctx.check_with(
        ctx.check,
        "gsl",
        features='cxx cxxprogram',
        header_name="gsl/gsl_version.h",
        lib="gsl",
        uselib_store='gsl',
        **kwargs
        )
    
    ctx.env.HEPWAF_FOUND_GSL = 1
    return

## EOF ##
