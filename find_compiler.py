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

### ---------------------------------------------------------------------------
def options(ctx):
    ctx.load('compiler_c')
    ctx.load('compiler_cxx')
    ctx.load('compiler_fc')
    return

### ---------------------------------------------------------------------------
def configure(ctx):
    return

### ---------------------------------------------------------------------------
@conf
def find_c_compiler(ctx, **kwargs):
    # prevent hysteresis
    if ctx.env.HEPWAF_FOUND_C_COMPILER:
        return

    comp = ctx.env.CFG_COMPILER
    for k,v in {
        'gcc': 'gcc',
        'icc': 'icc',
        'clang': 'clang',
        }.items():
        if comp.startswith(k):
            comp = v
            break
        pass

    ctx.env.CC = os.environ.get('CC', comp)
    ctx.load('c_config')
    ctx.load('compiler_c')

    ctx.env.HEPWAF_FOUND_C_COMPILER = 1
    return

### ---------------------------------------------------------------------------
@conf
def find_cxx_compiler(ctx, **kwargs):
    # prevent hysteresis
    if ctx.env.HEPWAF_FOUND_CXX_COMPILER:
        return

    comp = ctx.env.CFG_COMPILER
    for k,v in {
        'gcc': 'g++',
        'g++': 'g++',
        'icc': 'icc',
        'clang': 'clang++',
        }.items():
        if comp.startswith(k):
            comp = v
            break
        pass

    ctx.env.CXX = os.environ.get('CXX', comp)
    ctx.load('c_config')
    ctx.load('compiler_cxx')
    ctx.env.HEPWAF_FOUND_CXX_COMPILER = 1
    return

### ---------------------------------------------------------------------------
@conf
def find_fortran_compiler(ctx, **kwargs):
    # prevent hysteresis
    if ctx.env.HEPWAF_FOUND_FORTRAN_COMPILER:
        return

    #ctx.env.FC = os.environ.get('FC', comp)
    ctx.load('c_config')
    ctx.load('compiler_fc')

    ctx.env.HEPWAF_FOUND_FORTRAN_COMPILER = 1
    return

## EOF ##

