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
    return

def configure(ctx):
    ctx.load('hep-waftools-base', tooldir=_heptooldir)
    return

@conf
def find_posixlibs(ctx, **kwargs):
    
    if not ctx.env.CC or not ctx.env.CXX:
        msg.fatal('load a C or C++ compiler first')
        pass

    ctx.load('hep-waftools-base', tooldir=_heptooldir)

    # find libm
    ctx.check_with(
        ctx.check,
        "m",
        features='cxx cxxprogram',
        lib='m',
        uselib_store='m',
        **kwargs
        )

    # find dl
    ctx.check_with(
        ctx.check,
        "dl",
        features='cxx cxxprogram',
        lib='dl',
        uselib_store='dl',
        **kwargs
        )

    # find pthread
    ctx.check_with(
        ctx.check,
        "pthread",
        features='cxx cxxprogram',
        lib='pthread',
        uselib_store='pthread',
        **kwargs
        )

    # find libz
    ctx.check_with(
        ctx.check,
        "zlib",
        features='cxx cxxprogram',
        header_name="zlib.h",
        lib='z',
        uselib_store='z',
        **kwargs
        )

    # find bfd
    ctx.check_with(
        ctx.check,
        "bfd",
        features='cxx cxxprogram',
        defines=['PACKAGE=1','PACKAGE_VERSION=1',],
        header_name="bfd.h",
        lib='bfd',
        uselib_store='bfd',
        use='dl',
        **kwargs
        )

    # find rt
    if not ctx.is_darwin():
        ctx.check_with(
            ctx.check,
            "rt",
            features='cxx cxxprogram',
            lib='rt',
            uselib_store='rt',
            **kwargs
            )
        pass


    # test bfd
    ctx.check_cxx(
        msg="Checking bfd_init",
        okmsg="ok",
        fragment='''\
        #include "bfd.h"
        #include <iostream>

        int main(int argc, char* argv[]) {
          bfd_init();
          bfd_error_type err = bfd_get_error();
          return (int)err;
        }
        ''',
        use="bfd dl",
        #defines=['PACKAGE=1','PACKAGE_VERSION=1',],
        execute  = True,
        mandatory= True,
        )

    ctx.env.HEPWAF_FOUND_POSIXLIBS = 1
    return

## EOF ##
