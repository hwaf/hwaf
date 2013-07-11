# -*- python -*-

# stdlib imports
import os
import os.path as osp
import sys

# waf imports ---
import waflib.Options
import waflib.Utils
import waflib.Logs as msg
from waflib.Configure import conf

_heptooldir = osp.dirname(osp.abspath(__file__))
# add this directory to sys.path to ease the loading of other hepwaf tools
if not _heptooldir in sys.path: sys.path.append(_heptooldir)

WSCRIPT_FILE = 'wscript'
HSCRIPT_FILE = 'hscript.yml'

### ---------------------------------------------------------------------------
def options(ctx):
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
        pass
    ctx.add_option(
        '--relocate-from',
        default=None,
        help='top-level path to relocate against (default=${PREFIX})',
        )
    ctx.add_option(
        '--project-version',
        default=None,
        help='modify the project version used during build',
        )
    ctx.add_option(
        '--local-cfg',
        default=None,
        help="Path to the local config file listing all type of configuration infos")

    ctx.load('hwaf-system', tooldir=_heptooldir)
    ctx.load('hwaf-dist',   tooldir=_heptooldir)
    ctx.load('hwaf-project-mgr', tooldir=_heptooldir)
    ctx.load('hwaf-runtime', tooldir=_heptooldir)
    ctx.load('hwaf-rules', tooldir=_heptooldir)

    ctx.load('hwaf-cmtcompat', tooldir=_heptooldir)

    pkgdir = 'src'
    if osp.exists(pkgdir):
        pkgs = hwaf_find_suboptions(pkgdir)
        ctx.recurse(pkgs, mandatory=False)
    return

### ---------------------------------------------------------------------------
def configure(ctx):
    if ctx.options.local_cfg:
        fname = osp.abspath(ctx.options.local_cfg)
        ctx.start_msg("Manifest file")
        ctx.end_msg(fname)
        ok = ctx.read_cfg(fname)
        ctx.start_msg("Manifest file processing")
        ctx.end_msg(ok)
        pass

    if not ctx.env.HWAF_MODULES: ctx.env.HWAF_MODULES = []
    if not ctx.env.HWAF_ENV_SPY: ctx.env.HWAF_ENV_SPY = []

    ctx.load('hwaf-system', tooldir=_heptooldir)
    ctx.load('hwaf-dist',   tooldir=_heptooldir)
    ctx.load('hwaf-project-mgr', tooldir=_heptooldir)
    ctx.load('hwaf-runtime', tooldir=_heptooldir)
    ctx.load('hwaf-rules', tooldir=_heptooldir)

    ctx.load('hwaf-cmtcompat', tooldir=_heptooldir)

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
              'INSTALL_AREA_LIBDIR',
              'PREFIX',
              'DESTDIR',
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

    # configure project
    ctx._hwaf_configure_project()

    # display project infos...
    msg.info('='*80)
    ctx.msg('project',    '%s-%s' % (ctx.env.HWAF_PROJECT_NAME,
                                     ctx.env.HWAF_PROJECT_VERSION))
    ctx.msg('prefix',     ctx.env.PREFIX)
    if ctx.env.DESTDIR:
        ctx.msg('destdir',     ctx.env.DESTDIR)
        pass
    ctx.msg('pkg dir',    ctx.env.CMTPKGS)
    ctx.msg('variant',    ctx.env.CMTCFG)
    ctx.msg('arch',       ctx.env.CFG_ARCH)
    ctx.msg('OS',         ctx.env.CFG_OS)
    ctx.msg('compiler',   ctx.env.CFG_COMPILER)
    ctx.msg('build-type', ctx.env.CFG_TYPE)
    deps = ctx.hwaf_project_deps()
    if deps: deps = ','.join(deps)
    else:    deps = 'None'
    ctx.msg('projects deps', deps)
    ctx.msg('install-area', ctx.env.INSTALL_AREA)
    ctx.msg('njobs-max', waflib.Options.options.jobs)
    msg.info('='*80)

    # environment has been bootstrapped
    # loop back over ctx.options.xyz in case some environment variables
    # need to be expanded
    opts = [o for o in dir(ctx.options)]
    for k in opts:
        v = getattr(ctx.options, k)
        if v == None or not isinstance(v, type("")):
            continue
        v = waflib.Utils.subst_vars(v, ctx.env)
        setattr(ctx.options, k, v)
        pass

    # loading the tool which logs the environment modifications
    ctx.load('hwaf-spy-env', tooldir=_heptooldir)
    ctx.hwaf_setup_spy_env()
    return

def build(ctx):
    ctx.load('hwaf-system', tooldir=_heptooldir)
    ctx.load('hwaf-dist',   tooldir=_heptooldir)
    ctx.load('hwaf-project-mgr', tooldir=_heptooldir)
    ctx.load('hwaf-runtime', tooldir=_heptooldir)
    ctx.load('hwaf-rules', tooldir=_heptooldir)
    ctx.load('hwaf-spy-env', tooldir=_heptooldir)

    ctx.load('hwaf-cmtcompat', tooldir=_heptooldir)
    
    ctx._hwaf_create_project_hwaf_module()
    ctx._hwaf_load_project_hwaf_module(do_export=False)
    return

### ---------------------------------------------------------------------------
@conf
def hwaf_get_install_path(self, k, destdir=True):
    """
    Installation path obtained from ``self.dest`` and prefixed by the destdir.
    The variables such as '${PREFIX}/bin' are substituted.
    """
    dest = waflib.Utils.subst_vars(k, self.env)
    dest = dest.replace('/', os.sep)
    if destdir and self.env.DESTDIR:
        destdir = self.env.DESTDIR
        dest = os.path.join(destdir, osp.splitdrive(dest)[1].lstrip(os.sep))
        pass
    return dest

### ---------------------------------------------------------------------------
@conf
def hwaf_find_subpackages(self, directory='.'):
    srcs = []
    root_node = self.path.find_dir(directory)
    dirs = root_node.ant_glob('**/*', src=False, dir=True)
    for d in dirs:
        #msg.debug ("##> %s (type: %s)" % (d.abspath(), type(d)))
        node = d
        if node and (node.ant_glob(WSCRIPT_FILE) or
                     node.ant_glob(HSCRIPT_FILE)):
            srcs.append(d)
        pass
    return srcs

### ---------------------------------------------------------------------------
def hwaf_find_suboptions(directory='.'):
    pkgs = []
    for root, dirs, files in os.walk(directory):
        if WSCRIPT_FILE in files or HSCRIPT_FILE in files:
            pkgs.append(root)
            continue
    return pkgs

### ---------------------------------------------------------------------------
@conf
def find_at(ctx, check, what, where, **kwargs):

    def _subst(v):
        v = waflib.Utils.subst_vars(v, ctx.env)
        return v

    where = _subst(where)
    if not osp.exists(where):
        return False

    os_env = dict(os.environ)
    pkgp = os.getenv("PKG_CONFIG_PATH", "")
    try:
        WHAT = what.upper()
        ctx.env.stash()
        ctx.env[WHAT + "_HOME"] = where
        incdir = osp.join(where, "include")
        bindir = osp.join(where, "bin")
        libdir = osp.join(where, "lib")
        incdir = getattr(ctx.options, 'with_%s_includes' % what, incdir)
        libdir = getattr(ctx.options, 'with_%s_libs' % what, libdir)

        if isinstance(incdir, (list, tuple)):
            if len(incdir)>0: incdir=incdir[0]
            else:             incdir=osp.join(where, "include")
        if isinstance(libdir, (list, tuple)):
            if len(libdir)>0: libdir=libdir[0]
            else:             libdir=osp.join(where, "lib")
        
        ctx.env.prepend_value('PATH',  bindir)
        ctx.env.prepend_value('RPATH', libdir)
        ctx.env.prepend_value('LD_LIBRARY_PATH', libdir)
        os_keys = ("PATH", "RPATH", "LD_LIBRARY_PATH")
        if ctx.is_darwin():
            os_keys += ("DYLD_LIBRARY_PATH",)
            ctx.env.prepend_value('DYLD_LIBRARY_PATH', libdir)
            os.environ['DYLD_LIBRARY_PATH'] = os.sep.join(ctx.env['DYLD_LIBRARY_PATH'])
            pass
        pkgconf_path = osp.join(where, "lib/pkgconfig")
        ctx.env.prepend_value('PKG_CONFIG_PATH', pkgconf_path)
        ctx.to_log("Pkg config path: %s" % ctx.env.PKG_CONFIG_PATH)

        for kk in os_keys:
            os.environ[kk] = os.pathsep.join(ctx.env[kk]+[os.getenv(kk,'')]) 
            pass
            
        if pkgp:
            os.environ["PKG_CONFIG_PATH"] = os.pathsep.join((pkgconf_path,pkgp))
        else:
            os.environ["PKG_CONFIG_PATH"] = pkgconf_path
        if osp.exists(incdir):
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
        path = waflib.Utils.subst_vars(path, ctx.env)
        ctx.in_msg = 0
        ctx.to_log("Checking for %s in %s" % (what, path))
        if ctx.find_at(check, what, path, **kwargs):
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
    cfg.optionxform = str
    cfg.read([fname])
    # top-level config
    if cfg.has_section('hwaf-cfg'):
        section = 'hwaf-cfg'
        for k in ('cmtcfg', 'prefix', 'projects', 'cmtpkgs'):
            if cfg.has_option(section, k):
                #msg.info("....[%s]..." % k)
                if not (None == getattr(ctx.options, k)):
                    # user provided a value from command-line: that wins.
                    pass
                else:
                    v = cfg.get(section, k)
                    setattr(ctx.options, k, v)
                    #ctx.msg(k, v)
                    pass
                pass
        pass

    # env-level config
    if cfg.has_section('hwaf-env'):
        for k in cfg.options('hwaf-env'):
            # FIXME: make sure variable interpolation works at some point
            ctx.env[k] = cfg.get('hwaf-env', k)
            pass
        pass
    
    # pkg-level config
    for section in cfg.sections():
        #print "*** section=[%s]..." % section
        if not hasattr(ctx.options, 'with_%s' % section):
            continue
        v = getattr(ctx.options, 'with_%s' % section)
        #print "*** section=[%s]... >> %s" % (section, v)
        if not (v == None):
            # user provided a value from command-line
            continue
        if cfg.has_option(section, 'path'):
            v = cfg.get(section, 'path')
            setattr(ctx.options, 'with_%s' % section, v)
            pass
        if cfg.has_option(section, 'includes'):
            v = cfg.get(section, 'includes')
            setattr(ctx.options, 'with_%s_includes' % section, v)
            pass
        if cfg.has_option(section, 'libs'):
            v = cfg.get(section, 'libs')
            setattr(ctx.options, 'with_%s_libs' % section, v)
            pass
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
    if not self.env.HWAF_RUNTIME_ENVVARS:
        self.env.HWAF_RUNTIME_ENVVARS = []
        pass
    if msg.verbose:
        v = self.env[k]
        if v and isinstance(v, (list,tuple)) and len(v) != 1:
            raise KeyError("env[%s]=%s" % (k,v))
    self.env.append_unique('HWAF_RUNTIME_ENVVARS', k)
    return

### ------------------------------------------------------------------------
@conf
def declare_runtime_alias(self, dst, src):
    '''
    declare_runtime_alias declares an alias, alive at runtime.
    ex:
      ctx.declare_runtime_alias("athena", "athena.py")
      ctx.declare_runtime_alias("ll", "ls -l")
    '''
    if not self.env.HWAF_RUNTIME_ALIASES:
        self.env.HWAF_RUNTIME_ALIASES = []
        pass
    if msg.verbose:
        for alias in self.env.HWAF_RUNTIME_ALIASES:
            k,v = alias
            if k == dst:
                raise KeyError("the alias [%s] was already defined (to=%r)" % (k,v))
    self.env.append_unique('HWAF_RUNTIME_ALIASES', [(dst, src)])
    return

### ------------------------------------------------------------------------
@conf
def hwaf_declare_macro(self, name, value):
    '''
    hwaf_declare_macro declares a macro with name `name` and value `value`
    @param name: a string
    @param value: a string or a list of 1-dict {hwaf-tag:"value"}
           hwaf-tag can be a simple string or a tuple of strings.
    '''
    ## FIXME
    return

### ------------------------------------------------------------------------
@conf
def hwaf_macro_prepend(self, name, value):
    '''
    hwaf_macro_prepend prepends a value `value` to a macro named `name`
    @param name: a string
    @param value: a string or a list of 1-dict {hwaf-tag:"value"}
           hwaf-tag can be a simple string or a tuple of strings.
    '''
    ## FIXME
    return

### ------------------------------------------------------------------------
@conf
def hwaf_macro_append(self, name, value):
    '''
    hwaf_macro_append appends a value `value` to a macro named `name`
    @param name: a string
    @param value: a string or a list of 1-dict {hwaf-tag:"value"}
           hwaf-tag can be a simple string or a tuple of strings.
    '''
    ## FIXME
    return

### ------------------------------------------------------------------------
@conf
def hwaf_macro_remove(self, name, value):
    '''
    hwaf_macro_remove removes a value `value` to a macro named `name`
    @param name: a string
    @param value: a string or a list of 1-dict {hwaf-tag:"value"}
           hwaf-tag can be a simple string or a tuple of strings.
    '''
    ## FIXME
    return

### ------------------------------------------------------------------------
@conf
def hwaf_declare_tag(self, name, content):
    '''
    hwaf_declare_tag declares a tag with name `name` and `content`,
    a list of strings defining the associated content of that tag.
    @param name: a string
    @param content: a string or a list of strings

    e.x:
      ctx.hwaf_declare_tag("x86_64-slc6-gcc46-dbg",
                           content=["x86_64", "x86_64-slc6", "linux", "slc6", "gcc"])
    '''
    ## FIXME
    return

### ------------------------------------------------------------------------
@conf
def hwaf_path_prepend(self, name, value):
    '''
    hwaf_path_prepend prepends a value `value` to a path named `name`
    @param name: a string
    @param value: a string or a list of 1-dict {hwaf-tag:"value"}
           hwaf-tag can be a simple string or a tuple of strings.
    '''
    ## FIXME
    return

### ------------------------------------------------------------------------
@conf
def hwaf_path_append(self, name, value):
    '''
    hwaf_path_append appends a value `value` to a path named `name`
    @param name: a string
    @param value: a string or a list of 1-dict {hwaf-tag:"value"}
           hwaf-tag can be a simple string or a tuple of strings.
    '''
    ## FIXME
    return

### ------------------------------------------------------------------------
@conf
def hwaf_path_remove(self, name, value):
    '''
    hwaf_path_remove removes a value `value` to a path named `name`
    @param name: a string
    @param value: a string or a list of 1-dict {hwaf-tag:"value"}
           hwaf-tag can be a simple string or a tuple of strings.
    '''
    ## FIXME
    return

### ------------------------------------------------------------------------
@conf
def hwaf_export_module(self, fname=WSCRIPT_FILE):
    '''
    hwaf_export_module registers the ``fname`` file for export.
    it will be installed in the ${PREFIX}/share/hwaf directory to be picked
    up by dependent projects.
    '''
    if not self.env.HWAF_MODULES:
        self.env.HWAF_MODULES = []
        pass
    node = None
    if osp.isabs(fname): node = self.root.find_or_declare(fname)
    else:                node = self.path.find_node(fname)
    if not node: self.fatal("could not find [%s]" % fname)
    #msg.info("::: exporting [%s]" % node.abspath())
    self.env.append_unique('HWAF_MODULES', node.abspath())
    
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
    os_env_keys += self.env.HWAF_RUNTIME_ENVVARS
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
            pass
        pass
    bld_area = self.env['BUILD_INSTALL_AREA']

    if bld_area:
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
    else:
        env['LD_LIBRARY_PATH'] = os.pathsep.join(
            waflib.Utils.to_list(self.env['LD_LIBRARY_PATH'])
            +[os.environ.get('LD_LIBRARY_PATH','')])

        env['PATH'] = os.pathsep.join(
            waflib.Utils.to_list(self.env['PATH'])
            +[os.environ.get('PATH','')])

        env['PYTHONPATH'] = os.pathsep.join(
            waflib.Utils.to_list(self.env['PYTHONPATH'])
            +[os.environ.get('PYTHONPATH','')])

        if self.is_darwin():
            env['DYLD_LIBRARY_PATH'] = os.pathsep.join(
                waflib.Utils.to_list(self.env['DYLD_LIBRARY_PATH'])
                +[os.environ.get('DYLD_LIBRARY_PATH','')])
            pass
        pass
    if not self.is_windows():
        env['CPPFLAGS'] = ' '.join('-D'+k for k in self.env['DEFINES'])
        pass
    for k in (#'CPPFLAGS',
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

### ------------------------------------------------------------------------
@conf
def _get_pkg_name(self):
    # FIXME: should this be more explicit ?
    pkg_name = self.path.name
    return pkg_name

### ------------------------------------------------------------------------
@conf
def _get_pkg_version_defines(self):
    pkg_name = _get_pkg_name(self)
    pkg_vers = "%s-XX-XX-XX" % pkg_name
    pkg_defines = ['PACKAGE_VERSION="%s"' % pkg_vers,
                   'PACKAGE_VERSION_UQ=%s'% pkg_vers]
    cmt_dir_node = self.path.get_src().find_dir('cmt')
    if not cmt_dir_node:
        return pkg_defines
    version_cmt = cmt_dir_node.find_resource('version.cmt')
    if not version_cmt:
        return pkg_defines
    pkg_vers = version_cmt.read().strip()
    pkg_defines = ['PACKAGE_VERSION="%s"' % pkg_vers,
                   'PACKAGE_VERSION_UQ=%s'% pkg_vers]
    #msg.debug("*** %s %r" % (pkg_name, pkg_vers))
    return pkg_defines

## EOF ##
