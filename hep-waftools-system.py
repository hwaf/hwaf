# -*- python -*-

### imports -------------------------------------------------------------------
# stdlib imports ---
import os
import platform
import sys

# waf imports ---
from waflib.Configure import conf
import waflib.Logs as msg
import waflib.Utils

### ---------------------------------------------------------------------------
def options(ctx):
    ctx.add_option(
        '--cmtcfg',
        default=None,
        help="The build type. ex: x86_64-linux-gcc-opt")

    return

### ---------------------------------------------------------------------------
def configure(ctx):

    ctx.load('c_config')
    ctx.load('compiler_cc')
    ctx.load('compiler_cxx')
        
    cmtcfg = os.environ.get('CMTCFG', None)
    if not cmtcfg and ctx.options.cmtcfg:
        cmtcfg = ctx.options.cmtcfg
        pass

    cfg_arch = None
    cfg_os   = None
    cfg_comp = ctx.env.CC[0]
    cfg_type = None
    
    if not cmtcfg:
        msg.debug('detecting default CMTCFG...')
        cfg_type = 'opt'
        if ctx.is_darwin():    cfg_os = 'darwin'
        elif ctx.is_linux():   cfg_os = 'linux'
        elif ctx.is_freebsd(): cfg_os = 'freebsd'
        else:                  cfg_os = 'win'
            

        if ctx.is_host_32b():   cfg_arch = 'i686'
        elif ctx.is_host_64b(): cfg_arch = 'x86_64'
        else:                   cfg_arch = 'x86_64'

        cmtcfg = '-'.join([cfg_arch, cfg_os,
                           cfg_comp, cfg_type])
        pass
    
    o = cmtcfg.split('-')
    if len(o) != 4:
        msg.fatal(
            ("Invalid CMTCFG (%s). Expected ARCH-OS-COMP-OPT. " +
            "ex: x86_64-linux-gcc-opt") %
            ctx.env.CMTCFG)
    
    if o[1].startswith('mac'): o[1] = 'darwin'
    if o[1].startswith('slc'): o[1] = 'linux'

    #if o[2].startswith('gcc'):
    #    o[2] = 'gcc'

    ctx.env.CMTCFG = cmtcfg
    ctx.env.CFG_QUADRUPLET = o
    
    ctx.env.CFG_ARCH, \
    ctx.env.CFG_OS, \
    ctx.env.CFG_COMPILER, \
    ctx.env.CFG_TYPE = ctx.env.CFG_QUADRUPLET

    msg.info('='*80)
    #ctx.msg('project',    ctx.env.PROJNAME)
    ctx.msg('prefix',     ctx.env.PREFIX)
    #ctx.msg('pkg dir',    ctx.env.CMTPKGS)
    ctx.msg('variant',    ctx.env.CMTCFG)
    ctx.msg('arch',       ctx.env.CFG_ARCH)
    ctx.msg('OS',         ctx.env.CFG_OS)
    ctx.msg('compiler',   ctx.env.CFG_COMPILER)
    ctx.msg('build-type', ctx.env.CFG_TYPE)
    msg.info('='*80)
    
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
