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

def options(ctx):

    ctx.load('compiler_c compiler_cxx python')
    ctx.load('findbase', tooldir="hep-waftools")

    ctx.add_option(
        '--with-python',
        default=None,
        help="Look for python at the given path")
    return

def configure(ctx):
    ctx.load('compiler_c compiler_cxx')
    ctx.load('findbase platforms', tooldir="hep-waftools")
    return

@conf
def find_python(ctx, **kwargs):
    
    ctx.load('findbase platforms', tooldir="hep-waftools")

    if not ctx.env.CXX and not ctx.env.CC:
        msg.fatal('load a C or C++ compiler first')
        pass

    # FIXME: take it from a user configuration file ?
    pyversion = kwargs.get("version", (2,6))

    # FIXME: force python2. needed to be done *before* 'ctx.load(python)'
    try:    ctx.find_program('python2', var='PYTHON')
    except: ctx.find_program('python',  var='PYTHON')
    
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


