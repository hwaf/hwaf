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
        '--with-gccxml',
        default=None,
        help="Look for GCCXML at the given path")
    return

def configure(conf):
    conf.load('hep-waftools-base', tooldir=_heptooldir)
    return

@conf
def find_gccxml(ctx, **kwargs):
    
    if not ctx.env.CXX:
        msg.fatal('load a C++ compiler first')
        pass


    kwargs = ctx._findbase_setup(kwargs)
    kwargs['mandatory'] = kwargs.get('mandatory', False)

    path_list = []
    if ctx.options.with_gccxml:
        path_list.append(
            osp.join(ctx.options.with_gccxml, "bin")
            )
        pass

    ctx.find_program(
        "gccxml",
        var="GCCXML",
        path_list=path_list,
        **kwargs)
    
    ctx.env.HEPWAF_FOUND_GCCXML = 1
    return

## EOF ##
