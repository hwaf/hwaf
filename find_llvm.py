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
        '--with-llvm',
        default=None,
        help="Look for LLVM at the given path")
    return

def configure(conf):
    conf.load('hwaf-base', tooldir=_heptooldir)
    return

@conf
def find_llvm(ctx, **kwargs):
    
    if not ctx.env.HWAF_FOUND_C_COMPILER:
        ctx.fatal('load a C compiler first')
        pass

    if not ctx.env.HWAF_FOUND_CXX_COMPILER:
        ctx.fatal('load a C++ compiler first')
        pass


    # find LLVM
    llvm_cfg = "llvm-config"
    if getattr(ctx.options, 'with_llvm', None):
        topdir = ctx.options.with_llvm
        topdir = ctx.hwaf_subst_vars(topdir)
        llvm_cfg = osp.abspath(osp.join(topdir, "bin", "llvm-config"))
        pass

    
    ctx.find_program(llvm_cfg, var='LLVM-CONFIG',**kwargs)
    llvm_cfg = ctx.env['LLVM-CONFIG']

    ctx.check_with(
        ctx.check_cfg,
        "LLVM (static)",
        path=llvm_cfg,
        package="",
        uselib_store="LLVM-static",
        args="--cppflags --libs --ldflags",
        )

    version = ctx.check_cxx(
        msg="Checking LLVM version",
        okmsg="ok",
        fragment='''\
        #include "llvm/Config/config.h"
        #include <iostream>

        int main(int argc, char* argv[]) {
          std::cout << LLVM_VERSION_MAJOR << "." << LLVM_VERSION_MINOR
                    << std::flush;
          return 0;
        }
        ''',
        use="LLVM-static",
        define_name = "HWAF_LLVM_VERSION",
        define_ret = True,
        execute  = True,
        mandatory=True,
        )
    ctx.start_msg("LLVM version")
    ctx.end_msg(version)

    ctx.check_with(
        ctx.check_cfg,
        "LLVM",
        path=llvm_cfg,
        package="",
        uselib_store="LLVM",
        args="--cppflags --ldflags",
        )
    ctx.env['LIB_LLVM'] = ["LLVM-%s" % version]
    
    ctx.env.LLVM_VERSION = version
    ctx.env.HWAF_FOUND_LLVM = 1
    return

@conf
def find_libclang(ctx, **kwargs):
    if not ctx.env.HWAF_FOUND_C_COMPILER:
        ctx.fatal('load a C compiler first')
        pass

    if not ctx.env.HWAF_FOUND_CXX_COMPILER:
        ctx.fatal('load a C++ compiler first')
        pass

    if not ctx.env.HWAF_FOUND_LLVM:
        ctx.fatal('load a LLVM configuration first')
        pass


    # dynamic library
    ctx.env['INCLUDES_clang'] = ctx.env['INCLUDES_LLVM']
    ctx.env['LIBPATH_clang'] = ctx.env['LIBPATH_LLVM']
    ctx.env['LIB_clang'] = ['clang']

    # static library 'clang-static'
    ctx.env['INCLUDES_clang-static'] = ctx.env['INCLUDES_LLVM']
    ctx.env['STLIBPATH_clang-static'] = ctx.env['LIBPATH_LLVM']
    ctx.env['STLIB_clang-static'] = [
        "clang",
        "clangARCMigrate",
        "clangASTMatchers",
        "clangRewriteFrontend",
        "clangRewriteCore",
        "clangStaticAnalyzerCheckers",
        "clangStaticAnalyzerFrontend",
        "clangStaticAnalyzerCore",
        "clangTooling",

        "clangFrontendTool",
        "clangFrontend",
        "clangDriver",
        "clangSerialization",
        #"clangIndex",
        "clangParse",
        "clangSema",
        "clangEdit",
        "clangAnalysis",
        "clangCodeGen",
        "clangAST",
        "clangLex",
        "clangBasic",
        ]

    version = ctx.check_cxx(
        msg="Checking CLang version",
        okmsg="ok",
        fragment='''\
        #include "clang/Basic/Version.h"
        #include <iostream>

        int main(int argc, char* argv[]) {
          std::cout << CLANG_VERSION_STRING
                    << std::flush;
          return 0;
        }
        ''',
        use="clang LLVM",
        define_name = "HWAF_CLANG_VERSION",
        define_ret = True,
        execute  = True,
        mandatory=True,
        )
    ctx.start_msg("CLang version")
    ctx.end_msg(version)

    ctx.env.CLANG_VERSION = version
    ctx.env.HWAF_FOUND_CLANG = 1
    return

## EOF ##
