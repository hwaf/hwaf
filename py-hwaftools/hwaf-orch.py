# -*- python -*-

"""
support for worch metabuild system.
"""

## stdlib imports -------------------------------------------------------------
import os
import os.path as osp

## waflib imports -------------------------------------------------------------
from waflib.Configure import conf

def options(ctx):
    ctx.load('orch')
    # automatically load orch config
    if osp.exists('orch.cfg'):
        ctx.orch_config = 'orch.cfg'
        pass
    
    return

def configure(ctx):
    return

def build(ctx):
    return

@conf
def hwaf_load_orch(ctx):
    ctx.load('orch')
    return

## EOF ##
