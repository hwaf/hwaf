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
        '--with-valgrind',
        default=None,
        help="Look for Valgrind at the given path")
    return

def configure(ctx):
    ctx.load('hwaf-base', tooldir=_heptooldir)
    return

@conf
def find_valgrind(ctx, **kwargs):
    
    ctx.load('hwaf-base', tooldir=_heptooldir)

    if not ctx.env.HWAF_FOUND_C_COMPILER:
        ctx.fatal('load a C compiler first')
        pass

    if not ctx.env.HWAF_FOUND_CXX_COMPILER:
        ctx.fatal('load a C++ compiler first')
        pass

    path_list = waflib.Utils.to_list(kwargs.get('path_list', []))
    if getattr(ctx.options, 'with_valgrind', None):
        topdir = ctx.options.with_valgrind
        topdir = ctx.hwaf_subst_vars(topdir)
        path_list.append(osp.join(topdir, "bin"))
        pass

    kwargs['mandatory']=kwargs.get('mandatory', False)
    kwargs['path_list']=path_list

    
    ctx.find_program(
        'valgrind', 
        var='VALGRIND',
        **kwargs)
    
    ctx.check_with(
        ctx.check_cfg,
        "valgrind",
        package="valgrind",
        uselib_store="valgrind",
        args='--cflags --libs',
        **kwargs)

    # test valgrind
    version = ctx.check_cxx(
        msg="Checking valgrind",
        okmsg="ok",
        fragment='''\
        #include "valgrind/config.h"
        #include "valgrind/valgrind.h"
        #include <iostream>

        int main(int /*argc*/, char** /*argv*/) {
          std::cout << PACKAGE_VERSION << std::flush;
          return 0;
        }
        ''',
        use="valgrind",
        define_name = "HWAF_VALGRIND_VERSION",
        define_ret = True,
        execute  = True,
        mandatory= kwargs['mandatory'],
        )
    ctx.start_msg("valgrind version")
    ctx.end_msg(version)

    ctx.env.VALGRIND_VERSION = version

    ctx.env.HWAF_FOUND_VALGRIND = 1
    return

## EOF ##
