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
        '--with-clhep',
        default=None,
        help="Look for CLHEP at the given path")
    return

def configure(conf):
    conf.load('hwaf-base', tooldir=_heptooldir)
    return

@conf
def find_clhep(ctx, **kwargs):
    
    if not ctx.env.HWAF_FOUND_C_COMPILER:
        ctx.fatal('load a C compiler first')
        pass

    if not ctx.env.HWAF_FOUND_CXX_COMPILER:
        ctx.fatal('load a C++ compiler first')
        pass


    # find CLHEP
    clhep_cfg = "clhep-config"
    path_list = []
    if getattr(ctx.options, 'with_clhep', None):
        clhep_cfg = osp.abspath(
            osp.join(ctx.options.with_clhep, "bin", "clhep-config")
            )
        path_list.append(
            osp.join(ctx.options.with_clhep, "bin")
            )
        pass
    kwargs['path_list']=path_list
    
    ctx.find_program(
        clhep_cfg, 
        var='CLHEP-CONFIG',
        **kwargs)
    clhep_cfg = ctx.env['CLHEP-CONFIG']

    ctx.check_with(
        ctx.check_cfg,
        "clhep",
        path=clhep_cfg,
        package="",
        uselib_store="CLHEP",
        args='--include --libs --ldflags',
        **kwargs)

    clhep_libs = '''\
    CLHEP-Cast
    CLHEP-Evaluator
    CLHEP-Exceptions
    CLHEP-GenericFunctions
    CLHEP-Geometry
    CLHEP-Matrix
    CLHEP-Random
    CLHEP-RandomObjects
    CLHEP-RefCount
    CLHEP-Vector
    '''

    for lib in clhep_libs.split():
        libname = lib.strip()
        for n in ('INCLUDES',
                  'LIBPATH',
                  'LINKFLAGS'):
            k = '%s_CLHEP'%n
            ctx.env[k] = [ 
                # sanitize paths
                p.replace("'", "").replace('"', '')
                for p in ctx.env[k] 
                ]
            ctx.env['%s_%s'%(n,libname)] = ctx.env[k][:]
        # massage -lCLHEP-$(version)
        # into -lCLHEP-$(sublib)-$(version)
        ctx.env['LIB_%s'%libname] = [l.replace('CLHEP',libname)
                                     for l in ctx.env['LIB_CLHEP']]
        pass

    version = ctx.check_cxx(
        msg="Checking clhep version",
        okmsg="ok",
        fragment='''\
        #include "CLHEP/ClhepVersion.h"
        #include <iostream>

        int main(int argc, char* argv[]) {
          std::cout << CLHEP::Version::String();
          return 0;
        }
        ''',
        use="CLHEP",
        define_name = "HWAF_CLHEP_VERSION",
        define_ret = True,
        execute  = True,
        mandatory=True,
        )
    ctx.start_msg("clhep version")
    ctx.end_msg(version)

    ctx.env.CLHEP_VERSION = version
    ctx.env.HWAF_FOUND_CLHEP = 1
    return

## EOF ##
