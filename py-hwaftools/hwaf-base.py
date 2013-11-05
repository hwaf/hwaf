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

### ---------------------------------------------------------------------------
def options(ctx):
    gr = ctx.get_option_group("configure options")
    if 'darwin' in sys.platform:
        gr.add_option(
            '--use-macports',
            default=None,
            action='store_true',
            help="Enable MacPorts")
        
        gr.add_option(
            '--use-fink',
            default=None,
            action='store_true',
            help="Enable Fink")
        pass
    gr.add_option(
        '--relocate-from',
        default=None,
        help='top-level path to relocate against (default=${PREFIX})',
        )
    gr.add_option(
        '--project-version',
        default=None,
        help='modify the project version used during build',
        )
    gr.add_option(
        '--local-cfg',
        default="local.conf",
        help="Path to the local config file listing all type of configuration infos")

    ctx.load('hwaf-system', tooldir=_heptooldir)
    ctx.load('hwaf-dist',   tooldir=_heptooldir)
    ctx.load('hwaf-project-mgr', tooldir=_heptooldir)
    ctx.load('hwaf-runtime', tooldir=_heptooldir)
    ctx.load('hwaf-rules', tooldir=_heptooldir)

    ctx.load('hwaf-cmtcompat', tooldir=_heptooldir)
    ctx.load('hwaf-orch', tooldir=_heptooldir)

    pkgdir = 'src'
    if osp.exists(pkgdir):
        pkgs = hwaf_find_suboptions(pkgdir)
        ctx.recurse(pkgs, mandatory=False)
    return

### ---------------------------------------------------------------------------
def configure(ctx):
    ctx.msg("hwaf version", os.environ.get("HWAF_VERSION", "N/A"))
    ctx.msg("hwaf revision", os.environ.get("HWAF_REVISION", "N/A"))

    # transfer all env.vars from OS to hwaf.ctx.env
    for k in os.environ:
        ctx.env[k] = os.environ[k]
        pass
    ##

    if ctx.options.local_cfg:
        fname = osp.abspath(ctx.options.local_cfg)
        ctx.msg("Manifest file", fname)
        ok = ctx.read_cfg(fname)
        ctx.msg("Manifest file processing", ok)
        pass

    if not ctx.env.HWAF_MODULES: ctx.env.HWAF_MODULES = []
    if not ctx.env.HWAF_ENV_SPY: ctx.env.HWAF_ENV_SPY = []

    ctx.load('hwaf-system', tooldir=_heptooldir)
    ctx.load('hwaf-dist',   tooldir=_heptooldir)
    ctx.load('hwaf-runtime', tooldir=_heptooldir)
    ctx.load('hwaf-project-mgr', tooldir=_heptooldir)
    ctx.load('hwaf-rules', tooldir=_heptooldir)

    ctx.load('hwaf-cmtcompat', tooldir=_heptooldir)
    ctx.load('hwaf-orch', tooldir=_heptooldir)

    # register a couple of runtime environment variables
    ctx.hwaf_declare_runtime_env('PATH')
    ctx.hwaf_declare_runtime_env('RPATH')
    ctx.hwaf_declare_runtime_env('LD_LIBRARY_PATH')
    ctx.hwaf_declare_runtime_env('PYTHONPATH')
    ctx.hwaf_declare_runtime_env('MANPATH')
    if ctx.is_darwin():
        ctx.hwaf_declare_runtime_env('DYLD_LIBRARY_PATH')
        pass
    ctx.hwaf_declare_runtime_env('PKG_CONFIG_PATH')
    ctx.hwaf_declare_runtime_env('HWAF_VARIANT')

    # explicitly declare paths
    ctx.hwaf_declare_path('PATH')
    ctx.hwaf_declare_path('RPATH')
    ctx.hwaf_declare_path('LD_LIBRARY_PATH')
    ctx.hwaf_declare_path('PYTHONPATH')
    ctx.hwaf_declare_path('MANPATH')
    if ctx.is_darwin():
        ctx.hwaf_declare_path('DYLD_LIBRARY_PATH')
        pass
    ctx.hwaf_declare_path('PKG_CONFIG_PATH')
    
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
              'FC'
              'LINK_CC',
              'LINK_CXX',
              'LINK_FC',

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
        ctx.hwaf_declare_runtime_env(k)
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
    ctx.msg('pkg dir',    ctx.env.PKGDIR)
    ctx.msg('variant',    ctx.env.HWAF_VARIANT)
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

    # configure orch, if needed
    ctx.hwaf_load_orch()
    
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

    # build orch, if needed
    ctx.hwaf_load_orch()
    
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
        if node and node.ant_glob(WSCRIPT_FILE):
            srcs.append(d)
        pass
    return srcs

### ---------------------------------------------------------------------------
def hwaf_find_suboptions(directory='.'):
    pkgs = []
    for root, dirs, files in os.walk(directory):
        if WSCRIPT_FILE in files:
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
        incdir = getattr(ctx.options, 'with_%s_incdir' % what, incdir)
        libdir = getattr(ctx.options, 'with_%s_libdir' % what, libdir)

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
            pass
        check(**this_kwargs)
        setattr(ctx.options, 'with_%s_incdir' % what, incdir)
        setattr(ctx.options, 'with_%s_libdir' % what, libdir)
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

    for path in [abspath(ctx.hwaf_subst_vars(p)) for p in paths if p]:
        ctx.in_msg = 0
        ctx.to_log("Checking for %s in %s" % (what, path))
        if ctx.find_at(check, what, path, **kwargs):
            #print ">> found %s at %s" % (what, path)
            ctx.in_msg = 0
            ctx.msg("Found %s at" % what, path, color="WHITE")
            ctx.hwaf_declare_runtime_env(WHAT + "_HOME")
            return
        pass

    ctx.in_msg = 0
    check(**kwargs)
    ctx.in_msg = 0
    ctx.msg("Found %s at" % what, "(local environment)", color="WHITE")
    # FIXME: handle windows ?
    ctx.env[WHAT + "_HOME"] = "/usr"
    ctx.hwaf_declare_runtime_env(WHAT + "_HOME")
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

    if 0:
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
        pass
    
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

    # make sure we initialize some waf-envs
    if not ctx.env.HWAF_TAGS:        ctx.env['HWAF_TAGS'] = {}
    if not ctx.env.HWAF_ACTIVE_TAGS: ctx.env['HWAF_ACTIVE_TAGS'] = []
    if not ctx.env.HWAF_PATH_VARS:   ctx.env['HWAF_PATH_VARS'] = []
    
    try: from ConfigParser import SafeConfigParser as CfgParser
    except ImportError: from configparser import ConfigParser as CfgParser
    cfg = CfgParser()
    cfg.optionxform = str
    cfg.read([fname])
    # top-level config
    if cfg.has_section('hwaf-cfg'):
        section = 'hwaf-cfg'
        for k in ('variant', 'prefix', 'projects', 'pkgdir'):
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
        # bootstrap-level tags
        if cfg.has_option(section, 'tags'):
            tags = cfg.get(section, 'tags')
            tags = waflib.Utils.to_list(tags)
            msg.debug('hwaf: enabling tags %r (from [hwaf-cfg/tags])...' % (tags,))
            for tag in tags:
                # first declare an empty tag
                ctx.hwaf_declare_tag(tag, content=[])
                # now, apply.
                ctx.hwaf_apply_tag(tag)
                pass
            pass
        pass

    # --- initial value for HWAF_VARIANT
    if getattr(ctx.options, 'variant', None):
        ctx.env.HWAF_VARIANT = ctx.options.variant
        pass
    
    # env-level config
    if cfg.has_section('hwaf-env'):
        for k in cfg.options('hwaf-env'):
            # FIXME: make sure variable interpolation works at some point
            ctx.env[k] = cfg.get('hwaf-env', k)
            pass
        pass

    def _as_string(v):
        if isinstance(v, (list, tuple)):
            if len(v)==1: v=v[0]
            else: raise ValueError('expected a 1-item collection (got: %r)' % v)
        return v

    # toolchain config
    if cfg.has_section('hwaf-toolchain'):
        section = 'hwaf-toolchain'
        secattr = section.replace('-','_')
        if cfg.has_option(section, 'path'):
            v = cfg.get(section, 'path')
            v = _as_string(v)
            setattr(ctx.options, 'with_%s' % secattr, v)
            
        if cfg.has_option(section, 'incdir'):
            v = cfg.get(section, 'incdir')
            v = _as_string(v)
            setattr(ctx.options, 'with_%s_incdir' % secattr, v)
            pass
        if cfg.has_option(section, 'libdir'):
            v = cfg.get(section, 'libdir')
            v = _as_string(v)
            setattr(ctx.options, 'with_%s_libdir' % secattr, v)
            pass
        pass
    
        
    # pkg-level config
    for section in cfg.sections():
        if section.startswith('hwaf-'):
            continue
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
            v = _as_string(v)
            setattr(ctx.options, 'with_%s' % section, v)
            pass
        if cfg.has_option(section, 'incdir'):
            v = cfg.get(section, 'incdir')
            v = _as_string(v)
            setattr(ctx.options, 'with_%s_incdir' % section, v)
            pass
        if cfg.has_option(section, 'libdir'):
            v = cfg.get(section, 'libdir')
            v = _as_string(v)
            setattr(ctx.options, 'with_%s_libdir' % section, v)
            pass
        pass
    return True

### ---------------------------------------------------------------------------
@conf
def hwaf_propagate_uselib(ctx, tgt, uses):
    if not uses:
        return
    for use in uses:
        for kk in ('INCLUDES',
                   'LIBPATH',   'LIB',
                   'STLIBPATH', 'STLIB'):
            vv = ctx.env['%s_%s' % (kk,use)]
            if vv:
                msg.debug('hwaf: propagate_uselib(%s_%s <<< %s)'% (kk,tgt, vv))
                ctx.env.append_unique('%s_%s' % (kk,tgt), vv)
                pass
            pass
        pass
    return

### ---------------------------------------------------------------------------
@conf
def hwaf_copy_uselib_defs(ctx, dst, src):
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
    ctx.env.append_unique('DEFINES', 'HAVE_%s=1' % dst.upper().replace('-','_'))
    return

### ---------------------------------------------------------------------------
@conf
def copy_uselib_defs(ctx, dst, src):
    return ctx.hwaf_copy_uselib_defs(dst, src)

### ---------------------------------------------------------------------------
@conf
def hwaf_define_uselib(self, name, libpath, libname, incpath, incname):
    """
    hwaf_define_uselib creates the proper uselib variables based on the ``name``
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
def hwaf_declare_runtime_env(self, k):
    '''
    hwaf_declare_runtime_env registers a particular key ``k`` as the name of an
    environment variable the project will need at runtime.
    '''
    if not self.env.HWAF_RUNTIME_ENVVARS:
        self.env.HWAF_RUNTIME_ENVVARS = []
        pass
    if msg.verbose and os.getenv('HWAF_DEBUG_RUNTIME', None):
        v = self.env[k]
        if v and isinstance(v, (list,tuple)) and len(v) != 1:
            raise KeyError("env[%s]=%s" % (k,v))
    self.env.append_unique('HWAF_RUNTIME_ENVVARS', k)
    return

### ------------------------------------------------------------------------
@conf
def hwaf_declare_runtime_alias(self, dst, src):
    '''
    hwaf_declare_runtime_alias declares an alias, alive at runtime.
    ex:
      ctx.hwaf_declare_runtime_alias("athena", "athena.py")
      ctx.hwaf_declare_runtime_alias("ll", "ls -l")
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
def hwaf_declare_macro(self, name, value, override=False):
    '''
    hwaf_declare_macro declares a macro with name `name` and value `value`
    @param name: a string
    @param value: a string or a list of 1-dict {hwaf-tag:"value"}
           hwaf-tag can be a simple string or a tuple of strings.
    @param override: if True, force value even if already pre-existing
    '''
    value = self._hwaf_select_value(value)
    if self.env[name]:
        old_value = self.hwaf_subst_vars(self.env[name])
        new_value = self.hwaf_subst_vars(value)
        if old_value != new_value and not override:
            raise waflib.Errors.WafError(
                "package [%s] re-declares pre-existing macro [%s]\n old-value=%r\n new-value=%r"
                % (self.hwaf_pkg_name(), name, old_value, new_value)
                )
    self.env[name] = value
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
    value = self._hwaf_select_value(value)
    if value:
        self.env.prepend_value(name, value)
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
    value = self._hwaf_select_value(value)
    if value:
        self.env.append_value(name, value)
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
    self.env['HWAF_TAGS'][name] = content
    if name in self.env['HWAF_ACTIVE_TAGS']:
        msg.debug("hwaf: re-applying tag [%s]..." % name)
        msg.debug("hwaf: re-applying tag [%s] - content: %s" % (name,content))
        self.hwaf_apply_tag(name)
    return

### ------------------------------------------------------------------------
@conf
def hwaf_apply_tag(self, *tag):
    '''
    hwaf_apply_tag activates a tag with name `tag`
    @param name: a string or a list of strings

    e.x:
      ctx.hwaf_apply_tag("x86_64-slc6-gcc46-dbg")
      ctx.hwaf_apply_tag("tag1 tag2")
      ctx.hwaf_apply_tag("tag1", "tag2")
    '''
    if isinstance(tag, type("")):
        tag = waflib.Utils.to_list(tag)
    for name in tag:
        try:
            name = self.hwaf_subst_vars(name)
            msg.debug("hwaf: applying tag [%s]..." % name)
            content = self.env['HWAF_TAGS'][name]
            self.env.append_unique('HWAF_ACTIVE_TAGS', [name])
            # FIXME: recursively apply_tag for content as well ?
            #        but then, a declare_tag for each tag content is needed!
            # for tag in content:
            #     if not tag in self.env.HWAF_ACTIVE_TAGS:
            #         self.hwaf_apply_tag(tag)
            self.env.append_unique('HWAF_ACTIVE_TAGS', content)
            msg.debug("hwaf: applying tag content: %s..." % (content,))
            msg.debug("hwaf: applying tag [%s]... [done]" % name)
        except KeyError:
            raise waflib.Errors.WafError("package [%s]: no such tag (%s) in HWAF_TAGS" % (self.path.name, name))
        pass
    pass

### ------------------------------------------------------------------------
@conf
def hwaf_has_tag(self, tag):
    '''
    hwaf_has_tag returns True if ``tag`` is a defined tag. (but not necessarily active)
    '''
    tag = self.hwaf_subst_vars(tag)
    return tag in self.env['HWAF_TAGS']

### ------------------------------------------------------------------------
@conf
def hwaf_enabled_tag(self, tag):
    '''
    hwaf_enabled_tag returns True if ``tag`` is a currently enabled tag
    '''
    tag = self.hwaf_subst_vars(tag)
    return tag in self.env['HWAF_ACTIVE_TAGS']

### ------------------------------------------------------------------------
@conf
def _hwaf_select_value(self, value):
    '''
    hwaf_select_value selects a value from the dict `value` corresponding
    to the set of currently live tags.
    '''
    msg.debug('hwaf: select default value: %s' % (value,))
    tags = self.env['HWAF_ACTIVE_TAGS']
    default = None
    def _select_tags(tag, tag_list):
        if isinstance(tag, type("")):
            return tag in tag_list
        for t in tag:
            if not t in tag_list:
                return False
        return True
    if isinstance(value, type("")):
        value = ({"default":value},)
    for d in value:
        v = list((k,v) for k,v in d.items())[0]
        msg.debug('hwaf: list= %s' % (v,))
        if isinstance(v[1], type("")):
            #msg.debug("hwaf: ==> v: %r\t tags=%r" %(v,tags))
            if _select_tags(v[0], tags):
                return waflib.Utils.subst_vars(v[1], self.env)
            if v[0] == "default":
                default = v[1]
                pass
        else:
            #msg.debug("hwaf: ++> v[1]: %r" %(v,))
            if _select_tags(v[0], tags):
                out = []
                for o in v[1]:
                    out.append(waflib.Utils.subst_vars(o, self.env))
                    pass
                #msg.debug("hwaf: selected= %s" % (out,))
                return out
            if v[0] == "default":
                default = v[1]
                pass
            pass
        pass
    #msg.debug('hwaf: select default value: %s' % (value,))
    if isinstance(default, type("")):
        return waflib.Utils.subst_vars(default, self.env)

    # check whether something was selected
    if default is None:
        return None

    out = []
    for o in default:
        out.append(waflib.Utils.subst_vars(o, self.env))
    return out

### ------------------------------------------------------------------------
@conf
def hwaf_declare_path(self, name, value=None):
    '''
    hwaf_declare_path declares a path `name` with value `value`
    @param name: a string
    @param value: a string or a list of 1-dict {hwaf-tag:"value"}
           hwaf-tag can be a simple string or a tuple of strings.
    '''
    self.hwaf_declare_runtime_env(name)
    self.env.append_unique('HWAF_PATH_VARS', name)
    if value is None:
        return
    value = self._hwaf_select_value(value)
    if self.env[name]:
        old_value = self.hwaf_subst_vars(self.env[name])
        new_value = self.hwaf_subst_vars(value)
        if old_value != new_value:
            raise waflib.Errors.WafError(
                "package [%s] re-declares pre-existing path [%s]\n old-value=%r\n new-value=%r"
                % (self.hwaf_pkg_name(), name, old_value, new_value)
                )
    self.env[name] = value
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
    self.env.append_unique('HWAF_PATH_VARS', name)
    value = self._hwaf_select_value(value)
    if value:
        self.env.prepend_value(name, value)
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
    self.env.append_unique('HWAF_PATH_VARS', name)
    value = self._hwaf_select_value(value)
    if value:
        self.env.append_value(name, value)
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
    self.env.append_unique('HWAF_PATH_VARS', name)
    remove = self._hwaf_select_value(value)
    if not remove:
        return
    cur_val = waflib.Utils.to_list(self.env[name])
    new_val = []
    for x in cur_val:
        ## FIXME: what are the CMT semantics ?
        if x == remove or remove in x:
            continue
        new_val.append(x)
        pass
    self.env[name] = new_val
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
    msg.debug("hwaf: exporting [%s]" % node.abspath())
    self.env.append_unique('HWAF_MODULES', node.abspath())
    if fname == WSCRIPT_FILE:
        return
    basename = node.name
    if basename.endswith('.py'): basename = basename[:-len('.py')]
    tooldir = node.parent.abspath()
    self.load(basename, tooldir=tooldir)
    
### ------------------------------------------------------------------------
@conf
def _hwaf_load_fct(ctx, pkgname, fname):
    import imp
    node = ctx.path.find_node(fname)
    if not node:
        ctx.fatal(
            "pkg [%s (dir=%s)]: file [%s] does not exist" %
            (pkgname, ctx.path.path_from(ctx.pkgdir), fname)
            )
    name = node.abspath()
    f = open(name, 'r')
    mod_name = '.'.join(['__hwaf__']+pkgname.split('/')+f.name[:-3].split('/'))
    mod = imp.load_source(mod_name, f.name, f)
    f.close()
    fun = getattr(mod, ctx.fun, None)
    if fun:
        fun(ctx)
    pass

### ------------------------------------------------------------------------
@conf
def hwaf_subst_vars(self, value, env=None):
    '''
    hwaf_subst_vars recursively calls waflib.Utils.subst_vars on `value` as
    long as a '${xxx}' variable is in the string
    '''
    if env is None: env=self.env
    
    orig_value = value
    i = 1024
    while i > 0:
        i -= 1
        value = " ".join(waflib.Utils.to_list(value))
        tmp = value
        value = waflib.Utils.subst_vars(value, env)
        msg.debug("hwaf: subst_vars(%r) -> %s" % (tmp, value,))
        if value.count('${') <= 0:
            return value
    self.fatal('package [%s] reached maximum recursive limit when resolving value %r' % orig_value)
    return

### ------------------------------------------------------------------------
@conf
def _hwaf_subenv(self, env=None):
    '''
    _hwaf_subenv returns a detached environment for a sub-feature.
    if ``env`` is a dict-like instance, it will be merged in.
    '''
    subenv = self.env.derive()
    subenv.detach()
    if env:
        env = dict(env)
        subenv.update(env)
        pass
    return subenv

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
              'FC',
              'LINK_CC',
              'LINK_CXX',
              'LINK_FC',
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
    pkg_name = self.hwaf_pkg_name(self.path)
    return osp.basename(pkg_name)

### ------------------------------------------------------------------------
@conf
def _get_pkg_version_defines(self):
    pkg_name = _get_pkg_name(self)
    pkg_vers = "%s-XX-XX-XX" % pkg_name
    pkg_defines = ['PACKAGE_VERSION="%s"' % pkg_vers,
                   'PACKAGE_VERSION_UQ=%s'% pkg_vers]

    # first: try version.hwaf
    version_hwaf = self.path.get_src().find_resource('version.hwaf')
    if version_hwaf:
        pkg_vers = version_hwaf.read().strip()
        pkg_defines = ['PACKAGE_VERSION="%s"' % pkg_vers,
                       'PACKAGE_VERSION_UQ=%s'% pkg_vers]
        return pkg_defines
    
    # then: try cmt/version.cmt
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

### ------------------------------------------------------------------------
import waflib.Build
_hwaf_orig_bld_call = waflib.Build.BuildContext.__call__
def _hwaf(self, *k, **kw):
    '''
    hwaf wraps the Build.BuildContext.__call__ method.

    e.x:
      ctx(
         features = "cxx cxxshlib",
         name = "mylib",
         source = "src/*.cxx",
      )
    '''
    #msg.info("ctx(%s, %s)" % (k, kw))
    ## FIXME:
    install_path = waflib.Utils.to_list(kw.get('install_path', []))
    if install_path:
        kw['install_path'] = install_path[0]
        pass

    # group = waflib.Utils.to_list(kw.get('group', []))
    # if group and len(group)==1 and group[0]:
    #     kw['group'] = group[0]
    #     pass

    features = waflib.Utils.to_list(kw.get('features', []))

    if 'hwaf_utest' in features: kw['group'] = 'test'
        
    ctx = self
    for x in features:
        try:
            #msg.info("--- trying [%s] ---..." % x)
            ctx = getattr(self, x)
            kw['features'] = [xx for xx in features if x != xx]
            #msg.info("--- trying [%s] ---... [ok]" % x)
            return ctx(*k, **kw)
        except AttributeError:
            ctx = self
            pass
        pass
    return _hwaf_orig_bld_call(ctx, *k, **kw)

waflib.Build.BuildContext.__call__ = _hwaf
del _hwaf

## EOF ##
