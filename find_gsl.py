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
        define_name = "HEPWAF_GSL_VERSION",
        define_ret = True,
        execute  = True,
        mandatory=True,
        )
    ctx.start_msg("GSL version")
    ctx.end_msg(version)

    ctx.env.GSL_VERSION = version
    ctx.env.HEPWAF_FOUND_GSL = 1
    return

## EOF ##
