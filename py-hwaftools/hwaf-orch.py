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
    #_heptooldir = osp.dirname(osp.abspath(__file__))
    ctx.load('hwaf-base')
    ctx.load('orch')
    return

def configure(ctx):
    ctx.load('hwaf-base')
    return

def build(ctx):
    return

@conf
def hwaf_load_orch(ctx):
    ctx.load('orch')
    return

## EOF ##
