# -*- python -*-

# stdlib imports
import os
import os.path as osp

# waf imports ---
import waflib.Utils
import waflib.Logs as msg
from waflib.Configure import conf

_heptooldir = osp.dirname(osp.abspath(__file__))

### ---------------------------------------------------------------------------
def options(ctx):
    ctx.load('hep-waftools-system', tooldir=_heptooldir)
    if 0 and ctx.is_darwin():
        ctx.add_option(
            '--use-macports',
            default=False,
            store_action=True,
            help="Enable MacPorts")
        
        ctx.add_option(
            '--use-fink',
            default=False,
            store_action=True,
            help="Enable Fink")
        
    return

### ---------------------------------------------------------------------------
def configure(ctx):
    ctx.load('hep-waftools-system', tooldir=_heptooldir)
    return

### ---------------------------------------------------------------------------
@conf
def find_at(conf, check, what, where, **kwargs):
    if not osp.exists(where):
        return False
        
    pkgp = os.getenv("PKG_CONFIG_PATH", "")
    try:
        conf.env.stash()
        conf.env[what + "_HOME"] = where
        conf.env.append_value('PATH',  osp.join(where, "bin"))
        conf.env.append_value('RPATH', osp.join(where, "lib"))
        pkgconf_path = osp.join(where, "lib/pkgconfig")
        conf.env.append_value('PKG_CONFIG_PATH', pkgconf_path)
        conf.to_log("Pkg config path: %s" % conf.env.PKG_CONFIG_PATH)
        
        if pkgp:
            os.environ["PKG_CONFIG_PATH"] = ":".join((pkgconf_path, pkgp))
        else:
            os.environ["PKG_CONFIG_PATH"] = pkgconf_path
        
        conf.parse_flags("-I%s/include -L%s/lib" % (where, where),
                         uselib_store=kwargs["uselib_store"])
        this_kwargs = kwargs.copy()
        this_kwargs['check_path'] = where
        check(**this_kwargs)
        return True
    except conf.errors.ConfigurationError:
        os.environ["PKG_CONFIG_PATH"] = pkgp
        conf.end_msg("failed", color="YELLOW")
        conf.env.revert()
        return False
    return False

### ---------------------------------------------------------------------------
@conf
def check_with(conf, check, what, *args, **kwargs):
    """
    Perform `check`, also looking at directories specified by the --with-X 
    commandline option and X_HOME environment variable (X = what.upper())
    
    The extra_args
    """
    import os
    from os.path import abspath
    
    with_dir = getattr(conf.options, "with_" + what, None)
    env_dir = os.environ.get(what.upper() + "_HOME", None)
    paths = [with_dir, env_dir] + kwargs.pop("extra_paths", [])
    
    WHAT = what.upper()
    kwargs["uselib_store"] = kwargs.get("uselib_store", WHAT)
    kwargs["use"] = waflib.Utils.to_list(kwargs.get("use", [])) + \
        waflib.Utils.to_list(kwargs["uselib_store"])

    if 1:
        for path in [abspath(p) for p in paths if p]:
            conf.to_log("Checking for %s in %s" % (what, path))
            if conf.find_at(check, WHAT, path, **kwargs):
                conf.msg("Found %s at" % what, path, color="WHITE")
                return

    check(**kwargs)
    conf.msg("Found %s at" % what, "(local environment)", color="WHITE")
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

    kwargs['extra_paths'] = kwargs.get('extra_paths', []) + extra_paths
    return kwargs

### ---------------------------------------------------------------------------
@conf
def read_cfg(ctx, fname):
    """
    read_cfg reads a MANIFEST-like file to extract a configuration.
    That configuration file must be in a format that ConfigParser understands.
    """
    return

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


## EOF ##
