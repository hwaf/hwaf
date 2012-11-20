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
    ctx.load('hep-waftools-base', tooldir=_heptooldir)
    ctx.add_option(
        '--with-tcmalloc',
        default=None,
        help="Look for TCMalloc at the given path")
    return

def configure(ctx):
    ctx.load('hep-waftools-base', tooldir=_heptooldir)
    return

@conf
def find_tcmalloc(ctx, **kwargs):
    
    if not ctx.env.CC or not ctx.env.CXX:
        msg.fatal('load a C or C++ compiler first')
        pass

    ctx.load('hep-waftools-base', tooldir=_heptooldir)

    path_list = []
    if ctx.options.with_tcmalloc:
        path_list.append(
            osp.join(ctx.options.with_sqlite, "bin")
            )
        pass

    kwargs['mandatory']=kwargs.get('mandatory', False)
    kwargs['path_list']=path_list

    
    ctx.check_with(
        ctx.check_cfg,
        "tcmalloc",
        package="libtcmalloc",
        uselib_store="tcmalloc",
        args='--cflags --libs',
        **kwargs)

    # test libtcmalloc
    version = ctx.check_cxx(
        msg="Checking libtcmalloc version",
        okmsg="ok",
        fragment='''\
        #include "gperftools/tcmalloc.h"
        #include <iostream>

        int main(int /*argc*/, char** /*argv*/) {
          std::cout << TC_VERSION_MAJOR << "." << TC_VERSION_MINOR << std::flush;
          if (TC_VERSION_PATCH != "") {
            std::cout << "." << TC_VERSION_PATCH << std::flush;
          }
          return 0;
        }
        ''',
        use="tcmalloc",
        define_name = "HEPWAF_TCMALLOC_VERSION",
        define_ret = True,
        execute  = True,
        mandatory= kwargs['mandatory'],
        )
    ctx.start_msg("tcmalloc version")
    ctx.end_msg(version)

    ctx.env.TCMALLOC_VERSION = version

    ctx.env.HEPWAF_FOUND_TCMALLOC = 1
    return

## EOF ##
