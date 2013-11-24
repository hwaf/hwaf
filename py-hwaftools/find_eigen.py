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
        '--with-eigen',
        default=None,
        help="Look for Eigen at the given path")
    return

def configure(conf):
    conf.load('hwaf-base', tooldir=_heptooldir)
    return

@conf
def find_eigen(ctx, **kwargs):
    
    if not ctx.env.HWAF_FOUND_CXX_COMPILER:
        ctx.fatal('load a C++ compiler first')
        pass

    # find Eigen
    path_list = waflib.Utils.to_list(kwargs.get('path_list', []))
    if getattr(ctx.options, 'with_eigen', None):
        topdir = ctx.options.with_eigen
        topdir = ctx.hwaf_subst_vars(topdir)
        if osp.exists(topdir):
            path_list.append(topdir)
            pass
        pass
    kwargs['path_list']=path_list
    incdirs = [osp.join(p, "include", "eigen3") for p in path_list]

    ctx.check_with(
        ctx.check,
        "eigen",
        features="cxx cxxprogram",
        header_name="Eigen/Eigen",
        uselib_store= "eigen",
        includes=incdirs,
        **kwargs
    )

    version = ctx.check_cxx(
        msg="Checking eigen version",
        okmsg="ok",
        fragment='''\
        #include "Eigen/Eigen"
        #include <iostream>

        int main(int argc, char* argv[]) {
          std::cout << EIGEN_WORLD_VERSION << "." 
                    << EIGEN_MAJOR_VERSION << "."
                    << EIGEN_MINOR_VERSION;
          return 0;
        }
        ''',
        use="eigen",
        define_name = "HWAF_EIGEN_VERSION",
        define_ret = True,
        execute  = True,
        mandatory=True,
        )
    ctx.msg("eigen version", version)

    #ctx.env.EIGEN_VERSION = version
    ctx.env.HWAF_FOUND_EIGEN = 1
    return

## EOF ##
