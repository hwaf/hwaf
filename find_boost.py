# -*- python -*-

# stdlib imports ---
import os
import os.path as osp
import subprocess

# waf imports ---
import waflib.Utils
import waflib.Logs as msg
from waflib.Configure import conf

#
_heptooldir = osp.dirname(osp.abspath(__file__))

def options(ctx):

    ctx.load('hwaf-base', tooldir=_heptooldir)

    ctx.load('boost')
    ctx.add_option(
        '--with-boost',
        default=None,
        help="Look for boost at the given path")
    return

def configure(ctx):
    ctx.load('hwaf-base', tooldir=_heptooldir)
    return

@conf
def find_boost(ctx, **kwargs):
    '''
    find_boost instructs hwaf to find a boost installation.
    keyword arguments are the same than of the waflib.extras.boost.check_boost
    function (see @waflib.extras.boost.)
    Relevant keyword args:
      "lib":      list of boost libraries to check
      "includes": path to the boost includes
      "libs":     path to boost libraries
    '''
    ctx.load('hwaf-base', tooldir=_heptooldir)

    if not ctx.env.HWAF_FOUND_C_COMPILER:
        ctx.fatal('load a C compiler first')
        pass

    if not ctx.env.HWAF_FOUND_CXX_COMPILER:
        ctx.fatal('load a C++ compiler first')
        pass

    if not ctx.env.HWAF_FOUND_PYTHON:
        ctx.load('find_python')
        ctx.find_python()
        pass

    xx,yy = ctx.env.PYTHON_VERSION.split(".")[:2]
    ctx.options.boost_python = "%s%s" % (xx,yy)

    for k in ('with_boost', 'with_boost_includes', 'with_boost_libs'):
        if not getattr(ctx.options, k, None):
            continue
        topdir = getattr(ctx.options, k)
        topdir = waflib.Utils.subst_vars(topdir, ctx.env)
        setattr(ctx.options, k, topdir)
        pass
    
    ctx.load('boost')
    boost_libs = kwargs.get('lib', '''\
    chrono date_time filesystem graph iostreams
    math_c99 math_c99f math_tr1 math_tr1f
    prg_exec_monitor program_options
    random regex serialization
    signals system thread 
    unit_test_framework wave wserialization
    ''')
    kwargs['lib'] = boost_libs
    
    kwargs['mt'] = kwargs.get('mt', False)
    kwargs['static'] = kwargs.get('static', False)
    kwargs['use'] = waflib.Utils.to_list(kwargs.get('use', [])) + ['python']

    # get include/lib-dir from command-line or from API
    kwargs['includes'] = getattr(ctx.options, 'with_boost_includes', kwargs.get('includes', None))
    kwargs['libs'] = getattr(ctx.options, 'with_boost_libs', kwargs.get('libs', None))

    # rationalize types
    if kwargs['libs'] is None: kwargs['libs'] = []
    if kwargs['includes'] is None: kwargs['includes'] = []

    # waflib.boost only checks under /usr/lib
    # for machines where dual-libs (32/64) are installed, also inject:
    if ctx.is_64b():
        libpath = [
            '/usr/lib64', '/usr/local/lib64', '/opt/local/lib64',
            '/sw/lib64', '/lib64',
            ]
        import waflib.extras.boost as _mod
        if _mod.BOOST_LIBS[0] != libpath[0]:
            _mod.BOOST_LIBS = libpath + _mod.BOOST_LIBS
        pass
    # clean-up non existing directories
    libdirs = []
    for dirname in waflib.Utils.to_list(kwargs['libs']):
        dirname = waflib.Utils.subst_vars(dirname, ctx.env)
        d = ctx.root.find_dir(dirname)
        if not d: continue
        libdirs.append(dirname)
        pass
    kwargs['libs'] = libdirs[:]

    # also clean-up non existing directories in options.boost_{includes,libs}
    for k in ('boost_includes', 'boost_libs'):
        v = getattr(ctx.options, k, None)
        if not v: continue
        dirs = []
        for dirname in waflib.Utils.to_list(v):
            dirname = waflib.Utils.subst_vars(dirname, ctx.env)
            d = ctx.root.find_dir(dirname)
            if not d: continue
            dirs.append(dirname)
            pass
        setattr(ctx.options, k, dirs)
        pass

    # override default for uselib_store (default="BOOST")
    kwargs['uselib_store'] = "boost"

    # set with_boost_xxx variables for 'check_with' benefit
    setattr(ctx.options, 'with_boost_includes', kwargs['includes'])
    setattr(ctx.options, 'with_boost_libs',     kwargs['libs'])
    setattr(ctx.options, 'with_boost',
            getattr(ctx.options, 'with_boost') or
            osp.dirname(kwargs['libs'][0])
            )
    ctx.check_with(
        ctx.check_boost,
        "boost",
        **kwargs)

    ## hack for boost_python...
    _boost_libs_list = waflib.Utils.to_list(boost_libs)
    if _boost_libs_list:
        _boost_lib_name = _boost_libs_list[0]
        boost_lib_tmpl = [lib for lib in ctx.env['LIB_boost']
                          if _boost_lib_name in lib][0]
        boost_python = boost_lib_tmpl.replace("boost_"+_boost_lib_name,
                                              'boost_python')
        ctx.env['LIB_boost'] = ctx.env['LIB_boost'] + [boost_python]
    
        for libname in _boost_libs_list + ['python',]:
            libname = libname.strip()
            for n in ('INCLUDES',
                      'LIBPATH',
                      'LINKFLAGS'):
                ctx.env['%s_boost-%s'%(n,libname)] = ctx.env['%s_boost'%n][:]
            lib = []
            for i in ctx.env['LIB_boost']:
                if i.startswith("boost_%s-"%libname):
                    lib.append(i)
                    break
                if i == "boost_%s"%libname:
                    lib.append(i)
                    break
            else:
                msg.warn("could not find a linkopt for [boost_%s] among: %s" %
                         (libname,ctx.env['LIB_boost']))
            ctx.env['LIB_boost-%s'%libname] = lib[:]

    # register the boost module
    import sys
    modname = 'waflib.extras.boost'
    fname = sys.modules[modname].__file__
    if fname.endswith('.pyc'): fname = fname[:-1]
    ctx.hwaf_export_module(ctx.root.find_node(fname).abspath())

    ctx.env.HWAF_FOUND_BOOST = 1
    return


