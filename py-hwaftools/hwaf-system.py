# -*- python -*-

### imports -------------------------------------------------------------------
# stdlib imports ---
import os
import os.path as osp
import platform
import sys

# waf imports ---
from waflib.Configure import conf
import waflib.Context
import waflib.Logs as msg
import waflib.Utils

_heptooldir = osp.dirname(osp.abspath(__file__))

### ---------------------------------------------------------------------------
def options(ctx):
    gr = ctx.get_option_group("configure options")
    default_prefix = "install-area"
    gr.add_option(
        '--prefix',
        default='install-area',
        help='installation prefix [default: %r]' % default_prefix)

    gr.add_option(
        '--variant',
        default=None,
        help="The build type. ex: x86_64-linux-gcc-opt")
    gr.add_option(
        '--pkgdir',
        default=None,
        help="The directory where pkgs are located")

    ctx.load('hwaf-project-mgr', tooldir=_heptooldir)
    ctx.load('find_compiler',            tooldir=_heptooldir)
    return

### ---------------------------------------------------------------------------
def configure(ctx):

    #ctx.load('c_config')
    #ctx.load('compiler_cc')
    #ctx.load('compiler_cxx')

    variant = os.environ.get('HWAF_VARIANT', os.environ.get('CMTCFG', None))
    if not variant and ctx.options.variant:
        variant = ctx.options.variant
        pass

    cfg_arch = None
    cfg_os   = None
    cfg_comp = 'gcc'
    cfg_type = None
    
    if not variant or variant == 'default':
        msg.debug('hwaf: detecting default HWAF_VARIANT...')
        cfg_type = 'opt'
        if ctx.is_darwin():    cfg_os = 'darwin'
        elif ctx.is_linux():   cfg_os = 'linux'
        elif ctx.is_freebsd(): cfg_os = 'freebsd'
        else:                  cfg_os = 'win'
            

        if ctx.is_host_32b():   cfg_arch = 'i686'
        elif ctx.is_host_64b(): cfg_arch = 'x86_64'
        else:                   cfg_arch = 'x86_64'

        variant = '-'.join([cfg_arch, cfg_os,
                            cfg_comp, cfg_type])
        pass
    
    o = variant.split('-')
    if len(o) != 4:
        ctx.fatal(
            ("Invalid HWAF_VARIANT (%s). Expected ARCH-OS-COMP-OPT. " +
            "ex: x86_64-linux-gcc-opt") %
            variant)
    
    if o[1].startswith('mac'): o[1] = 'darwin'
    if o[1].startswith('slc'): o[1] = 'linux'

    #if o[2].startswith('gcc'):
    #    o[2] = 'gcc'

    ctx.env.HWAF_VARIANT = variant
    ctx.env.CFG_QUADRUPLET = o
    
    ctx.env.CFG_ARCH, \
    ctx.env.CFG_OS, \
    ctx.env.CFG_COMPILER, \
    ctx.env.CFG_TYPE = ctx.env.CFG_QUADRUPLET

    projname = waflib.Context.g_module.APPNAME
    if not projname:
        projname = osp.basename(os.getcwd())
        waflib.Context.g_module.APPNAME = projname
        pass
    ctx.env.HWAF_PROJECT_NAME = projname

    projvers = waflib.Context.g_module.VERSION
    if ctx.options.project_version:
        projvers = ctx.options.project_version
        pass
    waflib.Context.g_module.VERSION = projvers
    ctx.env.HWAF_PROJECT_VERSION = projvers
    
    if not ctx.env.HWAF_TAGS:        ctx.env['HWAF_TAGS'] = {}
    if not ctx.env.HWAF_ACTIVE_TAGS: ctx.env['HWAF_ACTIVE_TAGS'] = []
    if not ctx.env.HWAF_PATH_VARS:   ctx.env['HWAF_PATH_VARS'] = []

    pkgdir = os.environ.get('PKGDIR', None)
    if not pkgdir and ctx.options.pkgdir:
        pkgdir = ctx.options.pkgdir
        pass
    if not pkgdir:
        pkgdir = 'src'
        pass
    ctx.env.PKGDIR = pkgdir

    if ctx.options.destdir:
        ctx.env.DESTDIR = ctx.options.destdir
        pass

    ctx.env.PREFIX = ctx.options.prefix or "/usr"
    ctx.env.PREFIX = osp.abspath(ctx.env.get_flat('PREFIX'))

    relocate_from = ctx.options.relocate_from
    if not relocate_from:
        relocate_from = ctx.env.PREFIX
        pass
    ctx.env.HWAF_RELOCATE = relocate_from
    
    # take INSTALL_AREA from PREFIX
    ctx.env.INSTALL_AREA = ctx.env.PREFIX
    if ctx.env.DESTDIR:
        pass

    # percolate HWAF_VARIANT
    ctx.hwaf_declare_tag(ctx.env.HWAF_VARIANT, content=ctx.env.HWAF_VARIANT.split("-"))
    ctx.hwaf_apply_tag(ctx.env.HWAF_VARIANT)

    # backward compat
    ctx.env.CMTCFG = ctx.env.HWAF_VARIANT
    return

### ---------------------------------------------------------------------------
@conf
def is_dbg(ctx):
    return '-dbg' in ctx.env.HWAF_VARIANT
@conf
def is_opt(ctx):
    return '-opt' in ctx.env.HWAF_VARIANT
@conf
def is_64b(ctx):
    return 'x86_64' in ctx.env.HWAF_VARIANT
@conf
def is_32b(ctx):
    return not ctx.is_64b()#'i686' in ctx.env.HWAF_VARIANT

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
    elif ctx.is_freebsd():
        return '.so'
    else:
        raise RuntimeError('unhandled platform [%s]' % sys.platform)
