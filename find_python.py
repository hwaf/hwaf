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
    ctx.load('hep-waftools-base', tooldir=_heptooldir)
    ctx.add_option(
        '--with-python',
        default=None,
        help="Look for python at the given path")
    return

def configure(ctx):
    ctx.load('hep-waftools-base', tooldir=_heptooldir)
    return

@conf
def find_python(ctx, **kwargs):
    
    ctx.load('hep-waftools-base', tooldir=_heptooldir)

    if not ctx.env.CXX and not ctx.env.CC:
        msg.fatal('load a C or C++ compiler first')
        pass

    # FIXME: take it from a user configuration file ?
    pyversion = kwargs.get("version", (2,6))

    # FIXME: force python2. needed to be done *before* 'ctx.load(python)'
    try:    ctx.find_program('python2', var='PYTHON')
    except: ctx.find_program('python',  var='PYTHON')

    ctx.declare_runtime_env('PYTHON')
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
        ctx.env.append_unique(
            'CPPFLAGS',
            ['-D__extern_always_inline=inline',
             ])
        pass

    ctx.load('python')
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
    cmd = waflib.Utils.subst_vars('${PYTHON_CONFIG}', ctx.env)
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

    ctx.env.HEPWAF_FOUND_PYTHON = 1
    return

@conf
def find_python_module(ctx, module_name, condition='', **kwargs):
    
    ctx.load('hep-waftools-base', tooldir=_heptooldir)

    if not ctx.env.CXX and not ctx.env.CC:
        msg.fatal('load a C or C++ compiler first')
        pass

    if not ctx.env.HEPWAF_FOUND_PYTHON:
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

