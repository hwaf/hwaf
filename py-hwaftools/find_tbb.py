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
        '--with-tbb',
        default=None,
        help="Look for Intel TBB at the given path")
    return

def configure(ctx):
    ctx.load('hwaf-base', tooldir=_heptooldir)
    return

@conf
def find_tbb(ctx, **kwargs):
    
    ctx.load('hwaf-base', tooldir=_heptooldir)

    if not ctx.env.HWAF_FOUND_C_COMPILER:
        ctx.fatal('load a C compiler first')
        pass

    if not ctx.env.HWAF_FOUND_CXX_COMPILER:
        ctx.fatal('load a C++ compiler first')
        pass

    kwargs['mandatory'] = kwargs.get('mandatory', False)
    ctx.check_with(
        ctx.check,
        "tbb",
        features='cxx cxxprogram',
        header_name="tbb/tbb.h",
        lib='tbb',
        uselib_store='tbb',
        **kwargs
        )


    # test tbb
    version = ctx.check_cxx(
        msg="Checking tbb version",
        okmsg="ok",
        fragment='''\
        #include "tbb/tbb.h"
        #include <iostream>

        int main(int /*argc*/, char** /*argv*/) {
          std::cout << TBB_VERSION_MAJOR << "." << TBB_VERSION_MINOR
                    << std::flush;
          return 0;
        }
        ''',
        use="tbb",
        define_name = "HWAF_TBB_VERSION",
        define_ret = True,
        execute  = True,
        mandatory= kwargs['mandatory'],
        )
    ctx.start_msg("TBB version")
    ctx.end_msg(version)

    ctx.env.TBB_VERSION = version

    version = ctx.check_cxx(
        msg="Checking tbb linking",
        okmsg="ok",
        fragment='''\
        #include "tbb/tbb.h"
        #include <iostream>

        int main(int /*argc*/, char** /*argv*/) {
          std::cout << tbb::TBB_runtime_interface_version()
                    << std::flush;
          return 0;
        }
        ''',
        use="tbb",
        execute  = True,
        define_ret = True,
        mandatory= kwargs['mandatory'],
        )
    ctx.start_msg("TBB runtime interface")
    ctx.end_msg(version)
    
    ctx.env.HWAF_FOUND_TBB = 1
    return

## EOF ##
