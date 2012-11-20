# -*- python -*-

# stdlib imports
import os
import os.path as osp
import sys

# waf imports ---
import waflib.Utils
import waflib.Logs as msg
from waflib.Configure import conf

_heptooldir = osp.dirname(osp.abspath(__file__))
# add this directory to sys.path to ease the loading of other hepwaf tools
if not _heptooldir in sys.path: sys.path.append(_heptooldir)

### ---------------------------------------------------------------------------
def options(ctx):
    ctx.load('compiler_c compiler_cxx')
    if 'darwin' in sys.platform:
        ctx.add_option(
            '--use-macports',
            default=None,
            action='store_true',
            help="Enable MacPorts")
        
        ctx.add_option(
            '--use-fink',
            default=None,
            action='store_true',
            help="Enable Fink")
    ctx.add_option(
        '--use-cfg-file',
        default=None,
        help="Path to a config file holding version+paths to external s/w",
        )
    ctx.load('hep-waftools-system', tooldir=_heptooldir)

    return

### ---------------------------------------------------------------------------
def configure(ctx):
    if ctx.options.use_cfg_file:
        fname = osp.abspath(ctx.options.use_cfg_file)
        ctx.start_msg("Manifest file")
        ctx.end_msg(fname)
        ok = ctx.read_cfg(fname)
        ctx.start_msg("Manifest file processing")
        ctx.end_msg(ok)
        pass
    ctx.load('hep-waftools-system', tooldir=_heptooldir)
    # register a couple of runtime environment variables
    ctx.declare_runtime_env('PATH')
    ctx.declare_runtime_env('RPATH')
    ctx.declare_runtime_env('LD_LIBRARY_PATH')
    ctx.declare_runtime_env('PYTHONPATH')
    if ctx.is_darwin():
        ctx.declare_runtime_env('DYLD_LIBRARY_PATH')
        pass
    ctx.declare_runtime_env('PKG_CONFIG_PATH')
    ctx.declare_runtime_env('CMTCFG')

    for k in ['CPPFLAGS',
              'CFLAGS',
              'CCFLAGS',
              'CXXFLAGS',
              'FCFLAGS',

              'LINKFLAGS',
              'SHLINKFLAGS',
              'SHLIB_MARKER',
              
              'AR',
              'ARFLAGS',

              'CC',
              'CXX',
              'LINK_CC',
              'LINK_CXX',

              'LIBPATH',
              'DEFINES',

              'EXTERNAL_AREA',
              'INSTALL_AREA',
              'INSTALL_AREA_BINDIR',
              'PREFIX',
              'BINDIR',
              'LIBDIR',
              
              'HOME',
              'EDITOR',
              'USER',
              'LANG',
              'LC_ALL',
              'TERM',
              'TERMCAP',
              'HISTORY',
              'HISTSIZE',
              'PS1',
              'SHELL',
              'PWD',
              'OLDPWD',
              'DISPLAY',
              ]:
        ctx.declare_runtime_env(k)
        pass
    return

### ---------------------------------------------------------------------------
@conf
def find_at(ctx, check, what, where, **kwargs):
    if not osp.exists(where):
        return False

    os_env = dict(os.environ)
    pkgp = os.getenv("PKG_CONFIG_PATH", "")
    try:
        ctx.env.stash()
        ctx.env[what + "_HOME"] = where
        incdir = osp.join(where, "include")
        bindir = osp.join(where, "bin")
        libdir = osp.join(where, "lib")
        ctx.env.append_value('PATH',  bindir)
        ctx.env.append_value('RPATH', libdir)
        ctx.env.append_value('LD_LIBRARY_PATH', libdir)
        os_keys = ("PATH", "RPATH", "LD_LIBRARY_PATH")
        if ctx.is_darwin():
            os_keys += ("DYLD_LIBRARY_PATH",)
            ctx.env.append_value('DYLD_LIBRARY_PATH', libdir)
            os.environ['DYLD_LIBRARY_PATH'] = os.sep.join(ctx.env['DYLD_LIBRARY_PATH'])
            pass
        pkgconf_path = osp.join(where, "lib/pkgconfig")
        ctx.env.append_value('PKG_CONFIG_PATH', pkgconf_path)
        ctx.to_log("Pkg config path: %s" % ctx.env.PKG_CONFIG_PATH)

        for kk in os_keys:
            os.environ[kk] = os.pathsep.join(ctx.env[kk]+[os.getenv(kk,'')]) 
            pass
            
        if pkgp:
            os.environ["PKG_CONFIG_PATH"] = os.pathsep.join((pkgconf_path,pkgp))
        else:
            os.environ["PKG_CONFIG_PATH"] = pkgconf_path
        if osp.exists(incdir):
            def _subst(v):
                v = waflib.Utils.subst_vars(v, ctx.env)
                return v
            ctx.parse_flags(_subst("${CPPPATH_ST}") % incdir,
                            uselib_store=kwargs["uselib_store"])
        if osp.exists(libdir):
            ctx.parse_flags(_subst("${LIBPATH_ST}") % libdir,
                            uselib_store=kwargs["uselib_store"])
        this_kwargs = kwargs.copy()
        this_kwargs['check_path'] = where
        if check == ctx.check_cfg:
            # check if the special xyz-config binary exists...
            if not this_kwargs['package'] and not osp.exists(bindir):
                ctx.fatal("no such directory [%s]" % bindir)
                pass
        check(**this_kwargs)
        return True
    except ctx.errors.ConfigurationError:
        os.environ = os_env
        os.environ["PKG_CONFIG_PATH"] = pkgp
        ctx.end_msg("failed", color="YELLOW")
        ctx.env.revert()
        return False
    return False

### ---------------------------------------------------------------------------
@conf
def check_with(ctx, check, what, *args, **kwargs):
    """
    Perform `check`, also looking at directories specified by the --with-X 
    commandline option and X_HOME environment variable (X = what.upper())
    
    The extra_args
    """
    import os
    from os.path import abspath

    # adds 'extra_paths' and other defaults...
    kwargs = ctx._findbase_setup(kwargs)

    with_dir = getattr(ctx.options, "with_" + what, None)
    env_dir = os.environ.get(what.upper() + "_HOME", None)
    paths = [with_dir, env_dir] + kwargs.pop("extra_paths", [])
    
    WHAT = what.upper()
    kwargs["uselib_store"] = kwargs.get("uselib_store", WHAT)
    kwargs["use"] = waflib.Utils.to_list(kwargs.get("use", [])) + \
        waflib.Utils.to_list(kwargs["uselib_store"])

    for path in [abspath(p) for p in paths if p]:
        ctx.in_msg = 0
        ctx.to_log("Checking for %s in %s" % (what, path))
        if ctx.find_at(check, WHAT, path, **kwargs):
            #print ">> found %s at %s" % (what, path)
            ctx.in_msg = 0
            ctx.msg("Found %s at" % what, path, color="WHITE")
            ctx.declare_runtime_env(WHAT + "_HOME")
            return
        pass

    ctx.in_msg = 0
    check(**kwargs)
    ctx.in_msg = 0
    ctx.msg("Found %s at" % what, "(local environment)", color="WHITE")
    # FIXME: handle windows ?
    ctx.env[WHAT + "_HOME"] = "/usr"
    ctx.declare_runtime_env(WHAT + "_HOME")
    return

### ---------------------------------------------------------------------------
@conf
def _findbase_setup(ctx, kwargs):
    extra_paths = []
    if ctx.is_linux() or \
           ctx.is_freebsd() or \
           ctx.is_darwin():
        extra_paths.extend([
                #"/usr",
                #"/usr/local",
            ])

    # FIXME: should use use_macports...
    if ctx.is_darwin(): # and ctx.options.use_macports:
        extra_paths.extend([
                # macports
                "/opt/local",
            ])
    # FIXME: should use with_fink
    if ctx.is_darwin(): # and ctx.options.with_fink:
        extra_paths.extend([
                # fink
                "/sw",
            ])

    kwargs['extra_paths'] = waflib.Utils.to_list(
        kwargs.get('extra_paths', [])) + extra_paths
    kwargs['_check_mandatory'] = kwargs.get('mandatory', True)
    kwargs[       'mandatory'] = kwargs.get('mandatory', True)
    return kwargs

### ---------------------------------------------------------------------------
@conf
def read_cfg(ctx, fname):
    """
    read_cfg reads a MANIFEST-like file to extract a configuration.
    That configuration file must be in a format that ConfigParser understands.
    """
    fname = osp.abspath(fname)
    if not osp.exists(fname):
        ctx.fatal("no such file [%s]" % fname)
        return False

    try: from ConfigParser import SafeConfigParser as CfgParser
    except ImportError: from configparser import ConfigParser as CfgParser
    cfg = CfgParser()
    cfg.read([fname])
    # top-level config
    if cfg.has_section('hepwaf-cfg'):
        section = 'hepwaf-cfg'
        for k in ('cmtcfg', 'prefix'):
            if cfg.has_option(section, k):
                if not (None == getattr(ctx.options, k)):
                    # user provided a value from command-line: that wins.
                    pass
                else:
                    v = cfg.get(section, k)
                    setattr(ctx.options, k, v)
                    pass
                pass
        pass
    
    # pkg-level config
    for section in cfg.sections():
        if not hasattr(ctx.options, 'with_%s' % section):
            continue
        v = getattr(ctx.options, 'with_%s' % section)
        if not (v == None):
            # user provided a value from command-line
            continue
        if not cfg.has_option(section, 'path'):
            # no useful info
            continue
        v = cfg.get(section, 'path')
        setattr(ctx.options, 'with_%s' % section, v)
        pass
    return True

### ---------------------------------------------------------------------------
@conf
def copy_uselib_defs(ctx, dst, src):
    for n in ('LIB', 'LIBPATH',
              'STLIB', 'STLIBPATH',
              'LINKFLAGS', 'RPATH',
              'CFLAGS', 'CXXFLAGS',
              'DFLAGS',
              'INCLUDES',
              'CXXDEPS', 'CCDEPS', 'LINKDEPS',
              'DEFINES',
              'FRAMEWORK', 'FRAMEWORKPATH',
              'ARCH'):
        ctx.env['%s_%s' % (n,dst)] = ctx.env['%s_%s' % (n,src)]
    ctx.env.append_unique('DEFINES', 'HAVE_%s=1' % dst.upper())
    return

### ---------------------------------------------------------------------------
@conf
def define_uselib(self, name, libpath, libname, incpath, incname):
    """
    define_uselib creates the proper uselib variables based on the ``name``
    with the correct library-path ``libpath``, library name ``libname``,
    include-path ``incpath`` and header file ``incname``
    """
    ctx = self
    n = name
    if libpath:
        libpath = waflib.Utils.to_list(libpath)
        ctx.env['LIBPATH_%s'%n] = libpath
        pass

    if libname:
        libname = waflib.Utils.to_list(libname)
        ctx.env['LIB_%s'%n] = libname
        pass
    
    if incpath:
        incpath = waflib.Utils.to_list(incpath)
        ctx.env['INCLUDES_%s'%n] = incpath
        pass

    NAME = name.upper().replace('-','_')
    ctx.env.append_unique('DEFINES', 'HAVE_%s=1' % NAME)
    return

### ------------------------------------------------------------------------
@conf
def declare_runtime_env(self, k):
    '''
    declare_runtime_env register a particular key ``k`` as the name of an
    environment variable the project will need at runtime.
    '''
    if not self.env.HEPWAF_RUNTIME_ENVVARS:
        self.env.HEPWAF_RUNTIME_ENVVARS = []
        pass
    if msg.verbose:
        v = self.env[k]
        if v and not isinstance(v, str):
            raise KeyError("env[%s]=%s" % (k,v))
    self.env.append_unique('HEPWAF_RUNTIME_ENVVARS', k)
    
### ------------------------------------------------------------------------
@conf
def _get_env_for_subproc(self, os_env_keys=None):
    import os
    #env = dict(os.environ)
    #waf_env = dict(self.env)
    #for k,v in waf_env.items():
    env = dict(os.environ)
    #env = dict(self.env)
    if not os_env_keys:
        os_env_keys = []
    os_env_keys += self.env.HEPWAF_RUNTIME_ENVVARS
    for k,v in dict(self.env).items():
        if not k in os_env_keys:
            try:            del env[k]
            except KeyError:pass
            continue
        v = self.env[k]
        #print("-- %s %s %r" % (k, type(k), v))
        if isinstance(v, (list,tuple)):
            v = list(v)
            for i,_ in enumerate(v):
                if hasattr(v[i], 'abspath'):
                    v[i] = v[i].abspath()
                else:
                    v[i] = str(v[i])
                    pass
                pass
            # handle xyzPATH variables (LD_LIBRARY_PATH, PYTHONPATH,...)
            if k.lower().endswith('path'):
                #print (">>> %s: %r" % (k,v))
                env[k] = os.pathsep.join(v)
            else:
                env[k] = ' '.join(v)
        else:
            env[k] = str(v)
    bld_area = self.env['BUILD_INSTALL_AREA']

    env['LD_LIBRARY_PATH'] = os.pathsep.join(
        [os.path.join(bld_area,'lib')]
        +waflib.Utils.to_list(self.env['LD_LIBRARY_PATH'])
        +[os.environ.get('LD_LIBRARY_PATH','')])

    env['PATH'] = os.pathsep.join(
        [os.path.join(bld_area,'bin')]
        +waflib.Utils.to_list(self.env['PATH'])
        +[os.environ.get('PATH','')])

    env['PYTHONPATH'] = os.pathsep.join(
        [os.path.join(bld_area,'python')]
        +waflib.Utils.to_list(self.env['PYTHONPATH'])
        +[os.environ.get('PYTHONPATH','')])

    if self.is_darwin():
        env['DYLD_LIBRARY_PATH'] = os.pathsep.join(
            [os.path.join(bld_area,'lib')]
            +waflib.Utils.to_list(self.env['DYLD_LIBRARY_PATH'])
            +[os.environ.get('DYLD_LIBRARY_PATH','')])
        pass
    
    for k in ('CPPFLAGS',
              'CFLAGS',
              'CCFLAGS',
              'CXXFLAGS',
              'FCFLAGS',

              'LINKFLAGS',
              'SHLINKFLAGS',

              'AR',
              'ARFLAGS',

              'CC',
              'CXX',
              'LINK_CC',
              'LINK_CXX',
              ):
        v = self.env.get_flat(k)
        env[k] = str(v)
        pass

    env['SHLINKFLAGS'] += ' '+self.env.get_flat('LINKFLAGS_cshlib')
    env['SHEXT'] = self.dso_ext()[1:]
    for k,v in env.items():
        if not isinstance(v, str):
            raise KeyError("env[%s]=%s" % (k,v))
    return env
## EOF ##
