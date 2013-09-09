# -*- python -*-

# stdlib imports
import os
import os.path as osp
import sys

# waf imports ---
import waflib.Configure
import waflib.ConfigSet
import waflib.Utils
import waflib.Logs as msg
import waflib.Options

_heptooldir = osp.dirname(osp.abspath(__file__))

def options(ctx):
    ctx.load('hwaf-base', tooldir=_heptooldir)
    return

def configure(ctx):
    ctx.load('hwaf-base', tooldir=_heptooldir)
    return

def build(ctx):
    ctx.load('hwaf-base', tooldir=_heptooldir)
    return

### ---------------------------------------------------------------------------
@waflib.Configure.conf
def hwaf_configure(ctx):
    dirs = ctx.hwaf_pkg_dirs()
    for d in dirs:
        ctx.start_msg("configuring")
        ctx.end_msg(d)
        ctx.recurse(d)
    return

### ---------------------------------------------------------------------------
@waflib.Configure.conf
def hwaf_build(ctx):

    ctx.add_group('test')
    if ctx.cmd in ('build','check'):
        # schedule unit tests
        ctx.add_post_fun(ctx.hwaf_utest_summary)
        ctx.add_post_fun(ctx.hwaf_utest_set_exit_code)
        pass

    dirs = ctx.hwaf_pkg_dirs()
    ctx.recurse(dirs)
    ctx.add_post_fun(lambda _ : ctx._hwaf_install_project_infos())
    return

## EOF ##
    
