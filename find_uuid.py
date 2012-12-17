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
        '--with-uuid',
        default=None,
        help="Look for UUID at the given path")
    return

def configure(ctx):
    ctx.load('hep-waftools-base', tooldir=_heptooldir)
    return

@conf
def find_uuid(ctx, **kwargs):
    
    ctx.load('hep-waftools-base', tooldir=_heptooldir)

    if not ctx.env.HEPWAF_FOUND_C_COMPILER:
        ctx.fatal('load a C compiler first')
        pass

    if not ctx.env.HEPWAF_FOUND_CXX_COMPILER:
        ctx.fatal('load a C++ compiler first')
        pass

    # find libuuid
    ctx.check_with(
        ctx.check,
        "uuid",
        features='cxx cxxprogram',
        header_name="uuid/uuid.h",
        lib='uuid',
        uselib_store='uuid',
        **kwargs
        )


    # test uuid
    ctx.check_cxx(
        msg="Checking uuid_generate",
        okmsg="ok",
        fragment='''\
        #include "uuid/uuid.h"
        #include <iostream>

        int main(int argc, char* argv[]) {
          uuid_t out;
          uuid_generate(out);
          return 0;
        }
        ''',
        use="uuid",
        execute  = True,
        mandatory= True,
        )

    ctx.env.HEPWAF_FOUND_UUID = 1
    return

## EOF ##
