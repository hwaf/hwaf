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

def shell(ctx):
    ctx.load('hwaf-base', tooldir=_heptooldir)
    return

### ---------------------------------------------------------------------------
@waflib.Configure.conf
def hwaf_configure(ctx):
    dirs = ctx.hwaf_pkg_dirs()
    npkgs = len(dirs)
    fmt = "%%0%dd" % (len("%s" % npkgs),)
    hdr = "[%s/%s]" % (fmt,fmt)
    for i,d in enumerate(dirs):
        #ctx.msg("configuring", d)
        pkg = "[%s]:" % ctx.hwaf_pkg_name(d)
        msg.pprint('NORMAL', hdr % (i+1, npkgs), sep='')
        msg.pprint('GREEN', "%s configuring..." % pkg.ljust(60))
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
    
