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
        '--with-unwind',
        default=None,
        help="Look for unwind at the given path")
    return

def configure(ctx):
    ctx.load('hwaf-base', tooldir=_heptooldir)
    return

@conf
def find_unwind(ctx, **kwargs):
    
    ctx.load('hwaf-base', tooldir=_heptooldir)

    if not ctx.env.HWAF_FOUND_C_COMPILER:
        ctx.fatal('load a C compiler first')
        pass

    if not ctx.env.HWAF_FOUND_CXX_COMPILER:
        ctx.fatal('load a C++ compiler first')
        pass

    # find unwind
    ctx.check_with(
        ctx.check,
        "unwind",
        features='cxx cxxprogram',
        header_name="unwind.h",
        lib='unwind',
        uselib_store='unwind',
        #use='dl',
        **kwargs
        )

    # test unwind
    # FIXME: we should actually test the functionality rather than
    #        just checking this compiles...
    ctx.check_cxx(
        msg="Checking unwind",
        okmsg="ok",
        fragment='''\
        #include "unwind.h"
        #include <iostream>

        int main(int argc, char* argv[]) {
          struct _Unwind_Context *ctx=NULL;
          return 0;
        }
        ''',
        use="unwind",
        execute  = True,
        mandatory= True,
        )

    ctx.env.HWAF_FOUND_UNWIND = 1
    return

## EOF ##
