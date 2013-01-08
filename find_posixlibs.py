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
    return

def configure(ctx):
    ctx.load('hwaf-base', tooldir=_heptooldir)
    return

@conf
def find_posixlibs(ctx, **kwargs):
    
    ctx.load('hwaf-base', tooldir=_heptooldir)

    if not ctx.env.HWAF_FOUND_C_COMPILER:
        ctx.fatal('load a C compiler first')
        pass

    if not ctx.env.HWAF_FOUND_CXX_COMPILER:
        ctx.fatal('load a C++ compiler first')
        pass

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

    # find libiberty
    ctx.check_with(
        ctx.check,
        "iberty",
        features='c cprogram',
        header_name="libiberty.h",
        lib='iberty',
        uselib_store='iberty',
        **kwargs
        )

    # find bfd
    bfd_mandatory = kwargs.get('mandatory', True)
    if ctx.is_darwin():
        bfd_mandatory = kwargs.get('mandatory', False)
        pass
    bfd_kwargs = dict(kwargs)
    bfd_kwargs['mandatory'] = bfd_mandatory
    
    ctx.check_with(
        ctx.check,
        "bfd",
        features='cxx cxxprogram',
        defines=['PACKAGE="package-name"','PACKAGE_VERSION="package-version"',],
        header_name="bfd.h",
        lib='bfd',
        uselib_store='bfd',
        use='dl iberty',
        **bfd_kwargs
        )
    ctx.env.DEFINES_bfd = []

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
        #ifndef PACKAGE
        # define PACKAGE "package-name"
        #endif
        #ifndef PACKAGE_VERSION
        # define PACKAGE_VERSION 1
        #endif
        #include "bfd.h"
        #include <iostream>

        int main(int argc, char* argv[]) {
          bfd_init();
          bfd_error_type err = bfd_get_error();
          return (int)err;
        }
        ''',
        use="bfd dl iberty z",
        execute  = True,
        mandatory= bfd_mandatory,
        )

    ctx.env.HWAF_FOUND_POSIXLIBS = 1
    return

## EOF ##
