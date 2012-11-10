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
        '--with-aida',
        default=None,
        help="Look for AIDA at the given path")
    return

def configure(conf):
    conf.load('hep-waftools-base', tooldir=_heptooldir)
    return

@conf
def find_aida(ctx, **kwargs):
    
    if not ctx.env.CXX:
        msg.fatal('load a C++ compiler first')
        pass


    ctx.check_with(
        ctx.check,
        "aida",
        features='cxx cxxprogram',
        header_name="AIDA/AIDA.h",
        uselib_store='AIDA',
        **kwargs
        )
    
    # version = ctx.check_cxx(
    #     msg="Checking AIDA version",
    #     okmsg="ok",
    #     fragment='''\
    #     #include "AIDA/Version.h"
    #     #include <iostream>
    #
    #     int main(int argc, char* argv[]) {
    #       std::cout << AIDA::Version::String();
    #       return 0;
    #     }
    #     ''',
    #     use="AIDA",
    #     define_name = "HEPWAF_AIDA_VERSION",
    #     define_ret = True,
    #     execute  = True,
    #     mandatory=True,
    #     )
    # ctx.start_msg("AIDA version")
    # ctx.end_msg(version)

    ctx.env.HEPWAF_FOUND_AIDA = 1
    return

## EOF ##
