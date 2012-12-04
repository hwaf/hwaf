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
g_HEPWAF_PROJECT_INFO = 'project.info'

def options(ctx):
    ctx.load('hep-waftools-base', tooldir=_heptooldir)
    return

def configure(ctx):
    ctx.load('hep-waftools-base', tooldir=_heptooldir)
    #ctx.load('hep-waftools-project-mgr', tooldir=_heptooldir)
    return

def build(ctx):
    ctx.load('hep-waftools-base', tooldir=_heptooldir)
    #ctx.load('hep-waftools-project-mgr', tooldir=_heptooldir)
    return

### ---------------------------------------------------------------------------
@waflib.Configure.conf
def hepwaf_configure(ctx):
    ctx.recurse(ctx.hepwaf_pkg_dirs())
    return

### ---------------------------------------------------------------------------
@waflib.Configure.conf
def hepwaf_build(ctx):
    # pkgs = ctx.hepwaf_find_subpackages(ctx.env.CMTPKGS)
    # for pkg in pkgs:
    #     ctx.recurse(pkg.srcpath())
    #     pass
    ctx.recurse(ctx.hepwaf_pkg_dirs())

    ctx._hepwaf_install_project_infos()

    return

## EOF ##
    
