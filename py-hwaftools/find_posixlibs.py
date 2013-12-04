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
    ctx.load('find_gdb', tooldir=_heptooldir)
    return

def configure(ctx):
    ctx.load('hwaf-base', tooldir=_heptooldir)
    ctx.load('find_gdb', tooldir=_heptooldir)
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

    if not ctx.env.HWAF_FOUND_GDB:
        # gdb might have installed interesting libs (iberty, bfd)
        ctx.find_gdb(mandatory=False)
        pass
    
    # find libm
    ctx.check_with(
        ctx.check,
        "m",
        features='c cprogram',
        lib='m',
        uselib_store='m',
        **kwargs
        )

    # find dl
    ctx.check_with(
        ctx.check,
        "dl",
        features='c cprogram',
        lib='dl',
        uselib_store='dl',
        **kwargs
        )

    # find pthread
    ctx.check_with(
        ctx.check,
        "pthread",
        features='c cprogram',
        lib='pthread',
        uselib_store='pthread',
        **kwargs
        )

    # find libz
    ctx.check_with(
        ctx.check,
        "zlib",
        features='c cprogram',
        header_name="zlib.h",
        lib='z',
        uselib_store='z',
        **kwargs
        )

    extra_paths = waflib.Utils.to_list(kwargs.get('extra_paths',[]))
    if ctx.env.GDB_HOME:
        gdb = ctx.hwaf_subst_vars('${GDB_HOME}')
        extra_paths.append(gdb)
        pass

    # find libiberty
    iberty_mandatory = kwargs.get('iberty_mandatory', False)
    if ctx.is_darwin():
        iberty_mandatory = kwargs.get('iberty_mandatory', False)
        pass
    iberty_kwargs = dict(kwargs)
    iberty_kwargs['mandatory'] = iberty_mandatory
    iberty_kwargs['extra_paths'] = extra_paths
    
    ctx.check_with(
        ctx.check,
        "iberty",
        features='c cstlib',
        header_name="libiberty.h",
        stlib='iberty',
        uselib_store='iberty',
        **iberty_kwargs
        )
    if ctx.env.LIBPATH_iberty and 0:
        ctx.env.STLIBPATH_iberty = ctx.env.LIBPATH_iberty
        ctx.env.STLIB_iberty = ctx.env.LIB_iberty
        ctx.env.LIB_iberty = []
        ctx.env.LIBPATH_iberty = []
        pass

    # find bfd
    bfd_mandatory = kwargs.get('bfd_mandatory', False)
    bfd_kwargs = dict(kwargs)
    bfd_kwargs['mandatory'] = bfd_mandatory
    bfd_kwargs['extra_paths'] = extra_paths
    
    ctx.check_with(
        ctx.check,
        "bfd",
        features='c cstlib',
        defines=['PACKAGE="package-name"','PACKAGE_VERSION="package-version"',],
        header_name="bfd.h",
        stlib='bfd',
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
            features='c cprogram',
            lib='rt',
            uselib_store='rt',
            **kwargs
            )
        pass

    # test bfd
    ctx.check_cc(
        msg="Checking bfd_init",
        okmsg="ok",
        features='c cstlib',
        fragment='''\
        #ifndef PACKAGE
        # define PACKAGE "package-name"
        #endif
        #ifndef PACKAGE_VERSION
        # define PACKAGE_VERSION 1
        #endif
        #include "bfd.h"

        int test_bfd_init() {
          bfd_init();
          bfd_error_type err = bfd_get_error();
          return (int)err;
        }
        ''',
        use=['z', 'bfd', 'iberty', 'dl'],
        mandatory= bfd_mandatory,
        )

    ctx.env.HWAF_FOUND_POSIXLIBS = 1
    return

## EOF ##
