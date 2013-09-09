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
    ctx.add_option(
        '--hwaf-worch-config',
        default='worch.cfg',
        help='Give an orchestration configuration file.',
        )
    ctx.add_option(
        '--hwaf-worch-start',
        action = 'store',
        default = 'start',
        help='Set the section to start the orchestration',
        )

    # automatically load orch config
    if osp.exists('worch.cfg'):
        ctx.hwaf_worch_config = 'worch.cfg'
        pass
    
    return

def configure(ctx):
    return

def build(ctx):
    return

@conf
def hwaf_load_orch(ctx):
    orch_cfg = getattr(ctx.options, 'hwaf_worch_config', None)
    if orch_cfg and osp.exists(orch_cfg):
        ctx.options.orch_config = ctx.options.hwaf_worch_config
        ctx.options.orch_start = ctx.options.hwaf_worch_start
        ctx.load('orch.waffuncs')
    return

## EOF ##
