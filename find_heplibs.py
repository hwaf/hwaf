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
    'boost',
    'bzip',
    'cernroot',
    'clhep',
    'gccxml',
    'gsl',
    'hepmc',
    'heppdt',
    'lcgcmt',
    'lcg_cool',
    'lcg_coral',
    'lcg_pool',
    'sqlite',
    'tbb',
    'tcmalloc',
    'unwind',
    'uuid',
    'valgrind',
    'xrootd',
    )
    

def options(ctx):

    ctx.load('compiler_c compiler_cxx')
    ctx.load('findbase', tooldir="hep-waftools")

    for t in _heptools:
        ctx.load('find_%s' % t, tooldir="hep-waftools")
        pass
    
    return

def configure(ctx):
    ctx.load('compiler_c compiler_cxx')
    ctx.load('findbase platforms', tooldir="hep-waftools")

    for t in _heptools:
        ctx.load('find_%s' % t, tooldir="hep-waftools")
        pass
    
    return

## EOF ##
