# -*- python -*-

# stdlib imports ---
import os
import os.path as osp
import textwrap
import subprocess
try:
    subprocess.check_output
except AttributeError:
    def check_output(*popenargs, **kwargs):
        r"""Run command with arguments and return its output as a byte string.

        If the exit code was non-zero it raises a CalledProcessError.  The
        CalledProcessError object will have the return code in the returncode
        attribute and output in the output attribute.

        The arguments are the same as for the Popen constructor.  Example:

        >>> check_output(["ls", "-l", "/dev/null"])
        'crw-rw-rw- 1 root root 1, 3 Oct 18  2007 /dev/null\n'

        The stdout argument is not allowed as it is used internally.
        To capture standard error in the result, use stderr=STDOUT.

        >>> check_output(["/bin/sh", "-c",
        ...               "ls -l non_existent_file ; exit 0"],
        ...              stderr=STDOUT)
        'ls: non_existent_file: No such file or directory\n'
        """
        if 'stdout' in kwargs:
            raise ValueError('stdout argument not allowed, it will be overridden.')
        process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
        output, unused_err = process.communicate()
        retcode = process.poll()
        if retcode:
            cmd = kwargs.get("args")
            if cmd is None:
                cmd = popenargs[0]
            raise subprocess.CalledProcessError(retcode, cmd, output=output)
        return output
    subprocess.check_output = check_output
    pass

# waf imports ---
import waflib.Utils
import waflib.Logs as msg
from waflib.Configure import conf

#
_heptooldir = osp.dirname(osp.abspath(__file__))

def options(ctx):
    ctx.load('hwaf-base', tooldir=_heptooldir)
    ctx.add_option(
        '--with-python',
        default=None,
        help="Look for python at the given path")
    return

def configure(ctx):
    ctx.load('hwaf-base', tooldir=_heptooldir)
    return

@conf
def find_python(ctx, **kwargs):
    
    ctx.load('hwaf-base', tooldir=_heptooldir)

    # prevent hysteresis
    if ctx.env.HWAF_FOUND_PYTHON and not kwargs.get('override', False):
        return

    if not ctx.env.HWAF_FOUND_C_COMPILER:
        ctx.fatal('load a C compiler first')
        pass

    if not ctx.env.HWAF_FOUND_CXX_COMPILER:
        ctx.fatal('load a C++ compiler first')
        pass

    # FIXME: take it from a user configuration file ?
    pyversion = kwargs.get("version", None)

    # find python
    path_list = waflib.Utils.to_list(kwargs.get('path_list', []))
    if getattr(ctx.options, 'with_python', None):
        topdir = ctx.options.with_python
        topdir = ctx.hwaf_subst_vars(topdir)
        path_list.append(osp.join(topdir, "bin"))
        pass
    kwargs['path_list']=path_list


    ctx.find_program('python',  var='PYTHON', **kwargs)
    ctx.hwaf_declare_runtime_env('PYTHON')
    try:
        # temporary hack for clang and glibc-2.16
        # see: 
        # http://sourceware.org/git/?p=glibc.git;a=blobdiff;f=misc/sys/cdefs.h;h=fb6c959d903474b38fd0fcc36e17c5290dcd867c;hp=b94147efe8c5bbba718cb2f9d5911a92414864b6;hb=b7bfe116;hpb=43c4edba7ee8224134132fb38df5f63895cbb326
        ctx.check_cxx(
            msg="checking for __extern_always_inline",
            okmsg="ok",
            features="cxx cxxshlib",
            fragment=textwrap.dedent(
            '''\
            #define _FORTIFY_SOURCE 2
            #include <string.h>
            #include <sys/cdefs.h>
            int foo() { return 42; }
            '''),
            mandatory=True,
            )
    except waflib.Errors.ConfigurationError:
        ctx.env.append_unique('DEFINES',
                              ['__extern_always_inline=inline',])
        pass

    ctx.load('python')
    if pyversion:
        ctx.check_python_version(pyversion)
    # we remove the -m32 and -m64 options from these flags as they
    # can confuse 'check_python_headers' on darwin...
    save_flags = {}
    for n in ('CXXFLAGS','CFLAGS', 'LINKFLAGS'):
        save_flags[n] = ctx.env[n][:]
    if ctx.is_darwin():
        for n in ('CXXFLAGS','CFLAGS', 'LINKFLAGS'):
            ctx.env[n] = []
            for v in save_flags[n]:
                if v not in ('-m32', '-m64'):
                    ctx.env.append_unique(n, [v])

        pass
    ctx.check_python_headers()

    # restore these flags:
    for n in ('CXXFLAGS','CFLAGS', 'LINKFLAGS'):
        ctx.env[n] = save_flags[n][:]
        pass
        
    # hack for ROOT on macosx: LIBPATH_PYEMBED won't point at
    # the directory holding libpython.{so,a}
    pylibdir = ctx.env['LIBPATH_PYEMBED']
    cmd = ctx.hwaf_subst_vars('${PYTHON_CONFIG}')
    for arg in [#('--includes', 'INCLUDES'),
                ('--ldflags', 'LIBPATH'),
                #('--cflags', 'CXXFLAGS'),
                ]:
        o = subprocess.check_output(
            [cmd, arg[0]]
            )
        o = str(o)
        ctx.parse_flags(o, 'python')
    pylibdir = waflib.Utils.to_list(ctx.env['LIBPATH_python'])[:]

    # rename the uselib variables from PYEMBED to python
    ctx.copy_uselib_defs(dst='python', src='PYEMBED')
    
    ## the / in PYTHONARCHDIR and PYTHONDIR can confuse some clever software (rootcint)
    ## remove them from the DEFINES list, keep them in DEFINES_PYEMBED and DEFINES_PYEXT
    defines = [x for x in ctx.env["DEFINES"]
               if not (x.startswith("PYTHONARCHDIR=") or
                       x.startswith("PYTHONDIR"))]
    ctx.env["DEFINES"] = defines
    ctx.env["define_key"] = [
        k for k in ctx.env["define_key"]
        if not (x in ("PYTHONARCHDIR", "PYTHONDIR"))
        ]
    for py in ("PYEXT", "PYEMBED"):
        for k in ("PYTHONARCHDIR", "PYTHONDIR"):
            ctx.env.append_unique("DEFINES_%s" % py, "%s=%s" % (k, ctx.env.get_flat(k)))
            pass
        pass
    ####
    
    # FIXME: hack for python-lcg.
    # python-config --ldflags returns the wrong directory .../config...
    if pylibdir and \
           (osp.exists(osp.join(pylibdir[0],
                                'libpython%s.so'%ctx.env['PYTHON_VERSION']))
            or
            osp.exists(osp.join(pylibdir[0],
                                'libpython%s.a'%ctx.env['PYTHON_VERSION']))):
        ctx.env['LIBPATH_python'] = pylibdir[:]
    else:
        # PYEMBED value should be ok.
        pass
    
    # disable fat/universal archives on darwin
    if ctx.is_darwin():
        for n in ('CFLAGS', 'CXXFLAGS', 'LINKFLAGS'):
            args = []
            indices = []
            for i,a in enumerate(ctx.env['%s_python'%n]):
                if a == '-arch':
                    # removes ['-arch', 'x86_64']
                    indices.append(i)
                    indices.append(i+1)
            args = [a for i,a in enumerate(ctx.env['%s_python'%n])
                    if not (i in indices)]
            ctx.env['%s_python'%n] = args[:]
            
    # make sure the correct arch is built (32/64 !!)
    arch_flag = []
    if ctx.is_darwin():
        if ctx.is_32b(): arch_flag = ['-arch', 'i386']
        else:            arch_flag = ['-arch', 'x86_64']
    elif ctx.is_linux(): 
        if ctx.is_32b(): arch_flag = ['-m32',]
        else:            arch_flag = ['-m64',]
    elif ctx.is_freebsd(): 
        if ctx.is_32b(): arch_flag = ['-m32',]
        else:            arch_flag = ['-m64',]
    else:
        pass
    
    for n in ('CFLAGS', 'CXXFLAGS', 'LINKFLAGS'):
        ctx.env.append_unique('%s_python'%n, arch_flag)
        
    # disable the creation of .pyo files
    ctx.env['PYO'] = 0

    # retrieve the prefix
    cmd = [ctx.env.PYTHON_CONFIG, "--prefix"]
    lines=ctx.cmd_and_log(cmd).split()
    ctx.env["PYTHON_PREFIX"] = lines[0]
    ctx.env["LIBPATH_python"] = [l.replace("6464", "64")
                                 for l in ctx.env["LIBPATH_python"]]

    # register the python module
    import sys
    fname = sys.modules['waflib.Tools.python'].__file__
    if fname.endswith('.pyc'): fname = fname[:-1]
    ctx.hwaf_export_module(ctx.root.find_node(fname).abspath())

    ctx.env.HWAF_FOUND_PYTHON = 1
    return

@conf
def find_python_module(ctx, module_name, condition='', **kwargs):
    
    ctx.load('hwaf-base', tooldir=_heptooldir)

    if not ctx.env.CXX and not ctx.env.CC:
        msg.fatal('load a C or C++ compiler first')
        pass

    if not ctx.env.HWAF_FOUND_PYTHON:
        ctx.find_python()
        pass

    found = False
    os_env = dict(os.environ)
    try:
        ctx.env.stash()
        env = ctx._get_env_for_subproc()
        for k,v in env.items():
            os.environ[k] = v
            pass
        ctx.check_python_module(module_name, condition)
        found = True
    except ctx.errors.ConfigurationError:
        os.environ = os_env
        ctx.env.revert()
        found = False
        pass
    finally:
        os.environ = os_env
        pass

    if not found and kwargs.get('mandatory', True):
        ctx.fatal("python module %s not found" % module_name)
    return

