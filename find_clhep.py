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

    opt.load('compiler_c compiler_cxx')
    opt.load('findbase', tooldir=_heptooldir)

    opt.add_option(
        '--with-clhep',
        default=None,
        help="Look for CLHEP at the given path")
    return

def configure(conf):
    conf.load('compiler_c compiler_cxx')
    conf.load('findbase platforms', tooldir=_heptooldir)
    return

@conf
def find_clhep(ctx, **kwargs):
    
    if not ctx.env.CXX:
        msg.fatal('load a C++ compiler first')
        pass


    kwargs = ctx._findbase_setup(kwargs)
    
    # find CLHEP
    clhep_cfg = "clhep-config"
    if ctx.options.with_clhep:
        clhep_cfg = osp.abspath(
            osp.join(ctx.options.with_clhep, "bin", "clhep-config")
            )
        pass

    
    kwargs['mandatory'] = True
    
    ctx.find_program(clhep_cfg, var='CLHEP-CONFIG',**kwargs)
    clhep_cfg = ctx.env['CLHEP-CONFIG']
    
    ctx.check_cfg(
        path=clhep_cfg,
        package="",
        uselib_store="CLHEP",
        args='--cflags --include --libs --ldflags',
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
            ctx.env['%s_%s'%(n,libname)] = ctx.env['%s_CLHEP'%n][:]
        # massage -lCLHEP-$(version)
        # into -lCLHEP-$(sublib)-$(version)
        ctx.env['LIB_%s'%libname] = [l.replace('CLHEP',libname)
                                     for l in ctx.env['LIB_CLHEP']]
        pass

    ctx.env.HEPWAF_FOUND_CLHEP = 1
    return

## EOF ##
