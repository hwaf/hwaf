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
        '--with-hepmc',
        default=None,
        help="Look for HepMC at the given path")
    return

def configure(ctx):
    ctx.load('hwaf-base', tooldir=_heptooldir)
    return

@conf
def find_hepmc(ctx, **kwargs):
    
    ctx.load('hwaf-base', tooldir=_heptooldir)
    if not ctx.env.HWAF_FOUND_C_COMPILER:
        ctx.fatal('load a C compiler first')
        pass

    if not ctx.env.HWAF_FOUND_CXX_COMPILER:
        ctx.fatal('load a C++ compiler first')
        pass

    # find hepmc
    ctx.check_with(
        ctx.check,
        "HepMC",
        features='cxx cxxprogram',
        header_name="HepMC/Version.h",
        lib='HepMC',
        uselib_store='HepMC',
        **kwargs
        )

    # test
    version=ctx.check_cxx(
        msg="Checking HepMC::GenEvent",
        okmsg="ok",
        fragment='''\
        #include "HepMC/GenEvent.h"
        #include <iostream>

        int main(int argc, char* argv[]) {
          HepMC::GenEvent mc;
          return 0;
        }
        ''',
        use="HepMC",
        execute  = True,
        mandatory= True,
        )

    version = ctx.check_cxx(
        msg="Checking HepMC version",
        okmsg="ok",
        fragment='''\
        #include "HepMC/Version.h"
        #include <iostream>

        int main(int argc, char* argv[]) {
          std::cout << HEPMC_VERSION;
          return 0;
        }
        ''',
        use="HepMC",
        define_name = "HWAF_HEPMC_VERSION",
        define_ret = True,
        execute  = True,
        mandatory=True,
        )
    ctx.start_msg("HepMC version")
    ctx.end_msg(version)

    ctx.env.HEPMC_VERSION = version
    ctx.env.HWAF_FOUND_HEPMC = 1
    return

## EOF ##
