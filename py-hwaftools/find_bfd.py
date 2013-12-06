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
    ctx.load('find_iberty', tooldir=_heptooldir)
    ctx.load('find_z', tooldir=_heptooldir)
    ctx.load('find_dl', tooldir=_heptooldir)
    return

def configure(ctx):
    ctx.load('hwaf-base', tooldir=_heptooldir)
    ctx.load('find_gdb', tooldir=_heptooldir)
    ctx.load('find_iberty', tooldir=_heptooldir)
    ctx.load('find_z', tooldir=_heptooldir)
    ctx.load('find_dl', tooldir=_heptooldir)
    return

@conf
def find_bfd(ctx, **kwargs):
    
    ctx.load('hwaf-base', tooldir=_heptooldir)
    ctx.load('find_gdb', tooldir=_heptooldir)
    ctx.load('find_iberty', tooldir=_heptooldir)
    ctx.load('find_z', tooldir=_heptooldir)
    ctx.load('find_dl', tooldir=_heptooldir)

    if not ctx.env.HWAF_FOUND_C_COMPILER:
        ctx.fatal('load a C compiler first')
        pass

    if not ctx.env.HWAF_FOUND_GDB:
        # gdb might have installed interesting libs (iberty, bfd)
        ctx.find_gdb(mandatory=False)
        pass
    
    if not ctx.env.HWAF_FOUND_Z:
        ctx.find_z(mandatory=True)
        pass

    if not ctx.env.HWAF_FOUND_DL:
        ctx.find_dl(mandatory=True)
        pass

    if not ctx.env.HWAF_FOUND_IBERTY:
        ctx.find_iberty(mandatory=True)
        pass

    extra_paths = waflib.Utils.to_list(kwargs.get('extra_paths',[]))
    if ctx.env.GDB_HOME:
        gdb = ctx.hwaf_subst_vars('${GDB_HOME}')
        extra_paths.append(gdb)
        pass

    # find bfd
    ctx.check_with(
        ctx.check,
        "bfd",
        features='c cstlib',
        defines=['PACKAGE="package-name"','PACKAGE_VERSION="package-version"',],
        header_name="bfd.h",
        stlib='bfd',
        uselib_store='bfd',
        use='dl iberty',
        **kwargs
        )
    ctx.env.DEFINES_bfd = []

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
        mandatory= kwargs.get('mandatory', False),
        )

    ctx.env.HWAF_FOUND_BFD = 1
    return

## EOF ##
