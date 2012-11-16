# -*- python -*-

# stdlib imports ---
import os
import os.path as osp

# waf imports ---
import waflib.Utils
import waflib.Logs as msg
from waflib.Configure import conf

#

_heptools = (
    'aida',
    'boost',
    'bzip',
    'root',
    'clhep',
    'cmake',
    'gccxml',
    'gsl',
    'hepmc',
    'heppdt',
    'lcgcmt',
    'lcg_cool',
    'lcg_coral',
    'lcg_pool',
    'libxml2',
    'posixlibs',
    'python',
    'sqlite',
    'tbb',
    'tcmalloc',
    'unwind',
    'uuid',
    'valgrind',
    'xrootd',
    )
    
_heptooldir = osp.dirname(osp.abspath(__file__))

def options(ctx):

    ctx.load('compiler_c compiler_cxx')
    ctx.load('hep-waftools-base', tooldir=_heptooldir)

    for t in _heptools:
        ctx.load('find_%s' % t,  tooldir=_heptooldir)
        pass
    
    return

def configure(ctx):
    ctx.load('compiler_c compiler_cxx')
    ctx.load('hep-waftools-base', tooldir=_heptooldir)

    for t in _heptools:
        ctx.load('find_%s' % t, tooldir=_heptooldir)
        pass

    ctx.env.HEPWAF_HEPTOOLS = _heptools[:]
    return

## EOF ##
