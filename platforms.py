# -*- python -*-

### imports -------------------------------------------------------------------
# stdlib imports ---
import sys
import platform

# waf imports ---
from waflib.Configure import conf
import waflib.Logs as msg
import waflib.Utils

### ---------------------------------------------------------------------------
def options(ctx):
    return

### ---------------------------------------------------------------------------
def configure(ctx):
    return

### ---------------------------------------------------------------------------
@conf
def is_dbg(ctx):
    return '-dbg' in ctx.env.CMTCFG
@conf
def is_opt(ctx):
    return '-opt' in ctx.env.CMTCFG
@conf
def is_64b(ctx):
    return 'x86_64' in ctx.env.CMTCFG
@conf
def is_32b(ctx):
    return not ctx.is_64b()#'i686' in ctx.env.CMTCFG

@conf
def is_host_64b(ctx):
    #system, node, release, version, machine, processor = platform.uname()
    #return machine == 'x86_64'
    return '64bit' in platform.architecture()

@conf
def is_host_32b(ctx):
    return not ctx.is_host_64b()

@conf
def is_linux(ctx):
    return 'linux' in sys.platform

@conf
def is_freebsd(ctx):
    return 'freebsd' in sys.platform

@conf
def is_darwin(ctx):
    return 'darwin' in sys.platform

@conf
def is_windows(ctx):
    return waflib.Utils.is_win32
    #return 'win' in sys.platform

@conf
def dso_ext(ctx):
    if ctx.is_linux():
        return '.so'
    elif ctx.is_darwin():
        #return '.dylib'
        return '.so'
    elif ctx.is_windows():
        return '.dll'
    else:
        raise RuntimeError('unhandled platform [%s]' % sys.platform)
