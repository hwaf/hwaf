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
        '--with-sqlite',
        default=None,
        help="Look for SQLite at the given path")
    return

def configure(ctx):
    ctx.load('hep-waftools-base', tooldir=_heptooldir)
    return

@conf
def find_sqlite(ctx, **kwargs):
    
    if not ctx.env.CC or not ctx.env.CXX:
        msg.fatal('load a C or C++ compiler first')
        pass

    ctx.load('hep-waftools-base', tooldir=_heptooldir)

    path_list = []
    if getattr(ctx.options, 'with_sqlite', None):
        path_list.append(
            osp.join(ctx.options.with_sqlite, "bin")
            )
        pass

    kwargs['mandatory']=kwargs.get('mandatory', False)
    kwargs['path_list']=path_list

    
    ctx.find_program(
        'sqlite3', 
        var='SQLITE',
        **kwargs)
    
    ctx.check_with(
        ctx.check_cfg,
        "sqlite",
        package="sqlite3",
        uselib_store="sqlite",
        args='--cflags --libs',
        **kwargs)

    # test sqlite
    version = ctx.check_cxx(
        msg="Checking sqlite version",
        okmsg="ok",
        fragment='''\
        #include "sqlite3.h"
        #include <iostream>

        int main(int /*argc*/, char** /*argv*/) {
          std::cout << SQLITE_VERSION << std::flush;
          return 0;
        }
        ''',
        use="sqlite",
        define_name = "HEPWAF_SQLITE_VERSION",
        define_ret = True,
        execute  = True,
        mandatory= kwargs['mandatory'],
        )
    ctx.start_msg("sqlite version")
    ctx.end_msg(version)

    ctx.env.SQLITE_VERSION = version

    ctx.env.HEPWAF_FOUND_SQLITE = 1
    return

## EOF ##
