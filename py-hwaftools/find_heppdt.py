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
        '--with-heppdt',
        default=None,
        help="Look for HepPDT at the given path")
    return

def configure(ctx):
    ctx.load('hwaf-base', tooldir=_heptooldir)
    return

@conf
def find_heppdt(ctx, **kwargs):
    
    ctx.load('hwaf-base', tooldir=_heptooldir)

    if not ctx.env.HWAF_FOUND_C_COMPILER:
        ctx.fatal('load a C compiler first')
        pass

    if not ctx.env.HWAF_FOUND_CXX_COMPILER:
        ctx.fatal('load a C++ compiler first')
        pass

    # find heppdt
    ctx.check_with(
        ctx.check,
        "heppdt",
        features='cxx cxxprogram',
        header_name="HepPDT/Version.hh",
        lib='HepPDT',
        uselib_store='HepPDT',
        **kwargs
        )

    version = ctx.check_cxx(
        msg="Checking HepPDT version",
        okmsg="ok",
        fragment='''\
        #include "HepPDT/Version.hh"
        #include <iostream>

        int main(int argc, char* argv[]) {
          std::cout << HepPDT::versionName();
          return 0;
        }
        ''',
        use="HepPDT",
        define_name = "HWAF_HEPPDT_VERSION",
        define_ret = True,
        execute  = True,
        mandatory=True,
        )
    ctx.start_msg("HepPDT version")
    ctx.end_msg(version)

    ctx.env.HEPPDT_VERSION = version
    ctx.env.HWAF_FOUND_HEPPDT = 1


    # find heppid
    ctx.check_with(
        ctx.check,
        "heppdt", # yes... heppdt. re-use the same path for heppid
        features='cxx cxxprogram',
        header_name="HepPID/Version.hh",
        lib='HepPID',
        uselib_store='HepPID',
        **kwargs
        )

    version = ctx.check_cxx(
        msg="Checking HepPID version",
        okmsg="ok",
        fragment='''\
        #include "HepPID/Version.hh"
        #include <iostream>

        int main(int argc, char* argv[]) {
          std::cout << HepPID::versionName();
          return 0;
        }
        ''',
        use="HepPID",
        define_name = "HWAF_HEPPID_VERSION",
        define_ret = True,
        execute  = True,
        mandatory=True,
        )
    ctx.start_msg("HepPID version")
    ctx.end_msg(version)

    ctx.env.HEPPID_VERSION = version
    ctx.env.HWAF_FOUND_HEPPID = 1
    return

## EOF ##
