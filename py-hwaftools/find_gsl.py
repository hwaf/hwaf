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

    opt.load('hwaf-base', tooldir=_heptooldir)

    opt.add_option(
        '--with-gsl',
        default=None,
        help="Look for GSL at the given path")
    return

def configure(conf):
    conf.load('hwaf-base', tooldir=_heptooldir)
    return

@conf
def find_gsl(ctx, **kwargs):
    
    if not ctx.env.HWAF_FOUND_C_COMPILER:
        ctx.fatal('load a C compiler first')
        pass

    if not ctx.env.HWAF_FOUND_CXX_COMPILER:
        ctx.fatal('load a C++ compiler first')
        pass


    # find GSL
    gsl_cfg = "gsl-config"
    path_list = waflib.Utils.to_list(kwargs.get('path_list', []))
    if getattr(ctx.options, 'with_gsl', None):
        topdir = ctx.options.with_gsl
        topdir = ctx.hwaf_subst_vars(topdir)
        gsl_cfg = osp.abspath(osp.join(topdir, "bin", "gsl-config"))
        path_list.append(osp.join(topdir, "bin"))
        pass
    kwargs['path_list']=path_list
    
    ctx.find_program(
        gsl_cfg, 
        var='GSL-CONFIG',
        **kwargs)
    gsl_cfg = ctx.env['GSL-CONFIG']

    ctx.check_with(
        ctx.check_cfg,
        "gsl",
        package="",
        path="gsl-config",
        uselib_store="gsl",
        args='--cflags --libs --ldflags',
        **kwargs)

    version = ctx.check_cxx(
        msg="Checking GSL version",
        okmsg="ok",
        fragment='''\
        #include <gsl/gsl_version.h>
        #include <iostream>

        int main(int argc, char* argv[]) {
          std::cout << GSL_VERSION;
          return 0;
        }
        ''',
        use="gsl",
        define_name = "HWAF_GSL_VERSION",
        define_ret = True,
        execute  = True,
        mandatory=True,
        )
    ctx.msg("GSL version", version)

    ctx.env.GSL_VERSION = version
    ctx.env.HWAF_FOUND_GSL = 1
    return

## EOF ##
