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
    opt.load('hwaf-base', tooldir=_heptooldir)
    opt.add_option(
        '--with-xrootd',
        default=None,
        help="Look for xrootd at the given path")
    return

def configure(conf):
    conf.load('hwaf-base', tooldir=_heptooldir)
    return

@conf
def find_xrootd(ctx, **kwargs):
    
    if not ctx.env.HWAF_FOUND_C_COMPILER:
        ctx.fatal('load a C compiler first')
        pass

    if not ctx.env.HWAF_FOUND_CXX_COMPILER:
        ctx.fatal('load a C++ compiler first')
        pass


    ctx.check_with(
        ctx.check,
        "xrootd",
        features='cxx cxxprogram',
        header_name="xrootd/XrdVersion.hh",
        uselib_store='xrootd',
        **kwargs
        )

    bindir = osp.join(ctx.env.XROOTD_HOME, 'bin')
    libdir = osp.join(ctx.env.XROOTD_HOME, kwargs.get('libdir_name','lib'))
    incdir = osp.join(ctx.env.XROOTD_HOME, 'include')

    path_list = waflib.Utils.to_list(kwargs.get('path_list', []))
    path_list.append(bindir)
    kwargs['path_list'] = path_list
    
    ctx.hwaf_define_uselib(
        name="xrootd-posix", 
        libpath=libdir,
        libname="XrdPosix",
        incpath=incdir, 
        incname="xrootd/XrdPosix/XrdPosix.hh",
        )

    ctx.hwaf_define_uselib(
        name="xrootd-client",
        libpath=libdir,
        libname="XrdClient",
        incpath=incdir, 
        incname="xrootd/XrdClient/XrdClient.hh",
        )

    ctx.hwaf_define_uselib(
        name="xrootd-utils",
        libpath=libdir,
        libname="XrdUtils",
        incpath=incdir, 
        incname="xrootd/Xrd/XrdConfig.hh",
        )

    ctx.find_program(
        "xrdcp", 
        var="XRDCP-BIN", 
        **kwargs)

    kwargs['mandatory'] = False
    ctx.find_program(
        "xrootd", 
        var="XROOTD-BIN", 
        **kwargs)

    # -- check everything is kosher...
    version = ctx.check_cxx(
        msg="Checking xrootd version",
        okmsg="ok",
        fragment='''\
        #include "xrootd/XrdVersion.hh"
        #include <iostream>

        int main(int argc, char* argv[]) {
          std::cout << XrdVERSION << std::flush;
          return 0;
        }
        ''',
        use="xrootd",
        define_name = "HWAF_XROOTD_VERSION",
        define_ret = True,
        execute  = True,
        )
    ctx.start_msg("xrootd version")
    ctx.end_msg(version)

    ctx.env.XROOTD_VERSION = version
    ctx.env.HWAF_FOUND_XROOTD = 1
    return

## EOF ##
