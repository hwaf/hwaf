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
    ctx.recurse(ctx.hwaf_pkg_dirs())
    return

### ---------------------------------------------------------------------------
@waflib.Configure.conf
def hwaf_build(ctx):
    # pkgs = ctx.hwaf_find_subpackages(ctx.env.CMTPKGS)
    # for pkg in pkgs:
    #     ctx.recurse(pkg.srcpath())
    #     pass
    ctx.recurse(ctx.hwaf_pkg_dirs())

    ctx._hwaf_install_project_infos()
    return

## EOF ##
    
