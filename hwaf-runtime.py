# -*- python -*-

### imports -------------------------------------------------------------------
# stdlib imports ---
import os
import os.path as osp
import platform
import subprocess
import sys

# waf imports ---
from waflib.Configure import conf
import waflib.Context
import waflib.Logs as msg
import waflib.Task
import waflib.TaskGen
import waflib.Utils

_heptooldir = osp.dirname(osp.abspath(__file__))

### ---------------------------------------------------------------------------
class hwaf_runtime_tsk(waflib.Task.Task):
    """
    A task to properly configure runtime environment
    """
    color   = 'PINK'
    reentrant = False
    always = True
    
    def run(self):
        return
    
    pass # class hwaf_runtime_tsk

### ---------------------------------------------------------------------------
@conf
def hwaf_setup_runtime(self):
    feats = waflib.TaskGen.feats['hwaf_runtime_tsk']
    for fctname in feats:
        #msg.info("triggering [%s]..." % fctname)
        fct = getattr(waflib.TaskGen.task_gen, fctname, None)
        if fct:
            # extract un-decorated function...
            fct = getattr(fct, '__func__', fct)
            fct(self)
            pass
        #msg.info("triggering [%s]... [done]" % fctname)
    return

### ---------------------------------------------------------------------------
import waflib.Utils
from waflib.TaskGen import feature, before_method, after_method
@feature('hwaf_runtime_tsk', '*')
@before_method('process_rule')
def insert_project_level_bindir(self):
    '''
    insert_project_level_bindir adds ${INSTALL_AREA}/bin into the
    ${PATH} environment variable.
    '''
    _get = getattr(self, 'hwaf_get_install_path', None)
    if not _get: _get = getattr(self.bld, 'hwaf_get_install_path')
    d = _get('${INSTALL_AREA}/bin')
    self.env.prepend_value('PATH', d)
    return

### ---------------------------------------------------------------------------
import waflib.Utils
from waflib.TaskGen import feature, before_method, after_method
@feature('hwaf_runtime_tsk', '*')
@before_method('process_rule')
def insert_project_level_libdir(self):
    '''
    insert_project_level_bindir adds ${INSTALL_AREA}/lib into the
    ${LD_LIBRARY_PATH} and ${DYLD_LIBRARY_PATH} environment variables.
    '''
    _get = getattr(self, 'hwaf_get_install_path', None)
    if not _get: _get = getattr(self.bld, 'hwaf_get_install_path')
    d = _get('${INSTALL_AREA}/lib')
    self.env.prepend_value('LD_LIBRARY_PATH', d)
    self.env.prepend_value('DYLD_LIBRARY_PATH', d)
    return

### ---------------------------------------------------------------------------
import waflib.Utils
from waflib.TaskGen import feature, before_method, after_method
@feature('*')
@after_method('insert_project_level_bindir','insert_project_level_libdir')
def hwaf_setup_runtime_env(self):
    '''
    hwaf_setup_runtime_env crafts a correct os.environ from the ctx.env.
    '''
    env = _hwaf_get_runtime_env(self.bld)
    for k in self.env.HWAF_RUNTIME_ENVVARS:
        v = env.get(k, None)
        if v is None: continue
        os.environ[k] = v
    return


### ---------------------------------------------------------------------------
import waflib.Build
import waflib.Scripting
import waflib.Utils

class RunCmdContext(waflib.Build.BuildContext):
    """run a command within the correct runtime environment"""
    cmd = 'run'

    def execute_build(self):
        self.logger = msg

        lvl = msg.log.level
        if lvl < msg.logging.ERROR:
            msg.log.setLevel(msg.logging.ERROR)
            pass
        try:
            ret = super(RunCmdContext, self).execute_build()
        finally:
            msg.log.setLevel(lvl)

        #msg.info("args: %s" % waflib.Options.commands)
        if not waflib.Options.commands:
            self.fatal('%s expects at least one package name. got: %s' %
                       (self.cmd, waflib.Options.commands))

        args = []
        while waflib.Options.commands:
            arg = waflib.Options.commands.pop(0)
            #msg.info("arg: %r" % arg)
            args.append(arg)
            pass
        
        #msg.info("args: %s" % args)
        self.hwaf_setup_runtime()
        ret = hwaf_run_cmd_with_runtime_env(self, args)
        return ret
    pass # RunCmdContext

def _hwaf_get_runtime_env(ctx):
    """return an environment suitably modified to run locally built programs
    """
    import os
    cwd = os.getcwd()
    root = os.path.realpath(ctx.env.PREFIX)
    root = os.path.abspath(os.path.realpath(ctx.env.INSTALL_AREA))
    #msg.info(":::root:::"+root)
    if ctx.env.DESTDIR:
        root = ctx.env.DESTDIR + os.sep + ctx.env.INSTALL_AREA
        pass
    bindir = os.path.join(root, 'bin')
    libdir = os.path.join(root, 'lib')
    pydir  = os.path.join(root, 'python')

    env = dict(os.environ)

    def _env_prepend(k, args):
        old_v = env.get(k, '').split(os.pathsep)
        if isinstance(args, (list,tuple)):
            env[k] = os.pathsep.join(args)
        else:
            env[k] = args
            pass
        if old_v:
            env[k] = os.pathsep.join([env[k]]+old_v)
            pass
        return

    def _clean_env_path(env, k):
        paths = env.get(k, '').split(os.pathsep)
        o = []
        for p in paths:
            if osp.exists(p):
                o.append(p)
                pass
            #else: msg.info("discarding: %s" % p)
            pass
        env[k] = os.pathsep.join(o)
        return
    
    for k in ctx.env.keys():
        v = ctx.env[k]
        if k in ctx.env.HWAF_RUNTIME_ENVVARS:
            if isinstance(v, (list,tuple)):
                if len(v) == 1: v = v[0]
                else:
                    if k.endswith('PATH'): v = os.pathsep.join(v)
                    else:                  v = " ".join(v)
                pass
            # FIXME: we should have an API to decide...
            if k.endswith('PATH'): _env_prepend(k, osp.abspath(v))
            else:                  env[k]=v
            continue
        # reject invalid values (for an environment)
        if isinstance(v, (list,tuple)):
            continue
        env[k] = str(v)
        pass

    ## handle the shell flavours...
    if ctx.is_linux():
        shell = os.environ.get("SHELL", "/bin/sh")
    elif ctx.is_darwin():
        shell = os.environ.get("SHELL", "/bin/sh")
        shell = shell.strip()
        if shell.startswith('-'):
            shell = shell[1:]
    elif ctx.is_windows():
        ## FIXME: ???
        shell = None
    else:
        shell = None
        pass

    # catch-all
    if not shell or "(deleted)" in shell:
        # fallback on the *login* shell
        shell = os.environ.get("SHELL", "/bin/sh")
        pass

    env['SHELL'] = shell
    
        
    for k in env:
        v = env[k]
        if not isinstance(v, str):
            msg.warning('env[%s]=%r (%s)' % (k,v,type(v)))
            del env[k]

    for k in (
        'PATH',
        'LD_LIBRARY_PATH',
        'DYLD_LIBRARY_PATH',
        'PYTHONPATH',
        ):
        _clean_env_path(env, k)
        pass
    
    return env

def hwaf_run_cmd_with_runtime_env(ctx, cmds):
    # make sure we build first"
    # waflib.Scripting.run_command('install')
    
    import os
    import tempfile
    import textwrap

    #env = ctx.env
    cwd = os.getcwd()
    # get the runtime...
    env = _hwaf_get_runtime_env(ctx)

    for k in env:
        v = env[k]
        if not isinstance(v, str):
            ctx.fatal('env[%s]=%r (%s)' % (k,v,type(v)))
            pass
        pass

    shell_cmd = cmds[:]
    import pipes # FIXME: use shlex.quote when available ?
    from string import Template as str_template
    cmds=' '.join(pipes.quote(str_template(s).safe_substitute(env)) for s in cmds)

    retval = subprocess.Popen(
        cmds,
        env=env,
        cwd=os.getcwd(),
        shell=True,
        ).wait()

    if retval:
        signame = None
        if retval < 0: # signal?
            import signal
            for name, val in vars(signal).items():
                if len(name) > 3 and name[:3] == 'SIG' and name[3] != '_':
                    if val == -retval:
                        signame = name
                        break
        if signame:
            raise waflib.Errors.WafError(
                "Command '%s' terminated with signal %s." % (cmds, signame))
        else:
            raise waflib.Errors.WafError(
                "Command '%s' exited with code %i" % (cmds, retval))
        pass
    return retval

### ---------------------------------------------------------------------------
import waflib.Build
import waflib.Scripting
import waflib.Utils

class IShellContext(waflib.Build.BuildContext):
    """run an interactive shell with an environment suitably modified to run locally built programs"""
    cmd = 'shell'
    #fun = 'shell'

    def execute_build(self):
        self.logger = msg
        lvl = msg.log.level
        if lvl < msg.logging.ERROR:
            msg.log.setLevel(msg.logging.ERROR)
            pass
        try:
            ret = super(IShellContext, self).execute_build()
        finally:
            msg.log.setLevel(lvl)
        self.hwaf_setup_runtime()
        ret = hwaf_ishell(self)
        return ret
    
def hwaf_ishell(ctx):
    # make sure we build first"
    # waflib.Scripting.run_command('install')

    import os
    import tempfile
    import textwrap

    #env = ctx.env
    cwd = os.getcwd()
    root = os.path.realpath(ctx.options.prefix)
    root = os.path.abspath(os.path.realpath(ctx.env['INSTALL_AREA']))
    bindir = os.path.join(root, 'bin')
    libdir = os.path.join(root, 'lib')
    pydir  = os.path.join(root, 'python')

    # get the runtime...
    env = _hwaf_get_runtime_env(ctx)


    ## handle the shell flavours...
    if ctx.is_linux():
        shell = os.environ.get("SHELL", "/bin/sh")
    elif ctx.is_darwin():
        shell = os.environ.get("SHELL", "/bin/sh")
        shell = shell.strip()
        if shell.startswith('-'):
            shell = shell[1:]
    elif ctx.is_windows():
        ## FIXME: ???
        shell = None
    else:
        shell = None
        pass

    # catch-all
    if not shell or "(deleted)" in shell:
        # fallback on the *login* shell
        shell = os.environ.get("SHELL", "/bin/sh")

    tmpdir = tempfile.mkdtemp(prefix='hwaf-env-')
    dotrc = None
    dotrc_fname = None
    shell_cmd = [shell,]
    msg.info("---> shell: %s" % shell)

    shell_alias = '='
    if 'zsh' in os.path.basename(shell):
        env['ZDOTDIR'] = tmpdir
        dotrc_fname = os.path.join(tmpdir, '.zshrc')
        shell_cmd.append('-i')

    elif 'bash' in os.path.basename(shell):
        dotrc_fname = os.path.join(tmpdir, '.bashrc')
        shell_cmd += [
            '--init-file',
            dotrc_fname,
            '-i',
            ]
    elif 'csh' in os.path.basename(shell):
        msg.info('sorry, c-shells not handled at the moment: fallback to bash')
        dotrc_fname = os.path.join(tmpdir, '.bashrc')
        shell_cmd += [
            '--init-file',
            dotrc_fname,
            '-i',
            ]
        # FIXME: when c-shells are supported...
        # c-shells use a space as an alias separation token
        # in c-shell:
        #   alias ll 'ls -l'
        # in s-shell:
        #   alias ll='ls -l'
        #shell_alias = ' ' 
    else:
        # default to dash...
        dotrc_fname = os.path.join(tmpdir, '.bashrc')
        shell_cmd += [
            #'--init-file',
            #dotrc_fname,
            '-i',
            ]
        env['ENV'] = dotrc_fname
        pass

    ###

    hwaf_runtime_aliases = ";\n".join([
        "alias %s%s'%s'" % (alias[0], shell_alias, alias[1])
        for alias in ctx.env.HWAF_RUNTIME_ALIASES
        ])
    
    dotrc = open(dotrc_fname, 'w')
    dotrc.write(textwrap.dedent(
        '''
        ## automatically generated by hwaf-shell
        echo ":::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::"
        echo ":: launching a sub-shell with the correct environment..."
        echo ":: sourcing ${HOME}/%(dotrc_fname)s..."
        source ${HOME}/%(dotrc_fname)s
        echo ":: sourcing ${HOME}/%(dotrc_fname)s... [done]"

        # adjust env. variables
        export PATH=%(hwaf_path)s
        export LD_LIBRARY_PATH=%(hwaf_ld_library_path)s
        export DYLD_LIBRARY_PATH=%(hwaf_dyld_library_path)s
        export PYTHONPATH=%(hwaf_pythonpath)s

        # customize PS1 so we know we are in a hwaf subshell
        export PS1="[hwaf] ${PS1}"

        # setup aliases
        %(hwaf_runtime_aliases)s
        
        echo ":: hwaf environment... [setup]"
        echo ":: hit ^D or exit to go back to the parent shell"
        echo ":::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::"
        ''' % {
            'dotrc_fname' : os.path.basename(dotrc_fname),
            'hwaf_path': env['PATH'],
            'hwaf_ld_library_path': env['LD_LIBRARY_PATH'],
            'hwaf_dyld_library_path': env['DYLD_LIBRARY_PATH'],
            'hwaf_pythonpath': env['PYTHONPATH'],
            'hwaf_runtime_aliases': hwaf_runtime_aliases,
            }
        ))
    dotrc.flush()
    dotrc.close()

    for k in env:
        v = env[k]
        if not isinstance(v, str):
            ctx.fatal('env[%s]=%r (%s)' % (k,v,type(v)))
            pass
        pass
    
    retval = subprocess.Popen(
        shell_cmd,
        env=env,
        cwd=os.getcwd(),
        shell=True,
        ).wait()

    try:
        import shutil
        shutil.rmtree(tmpdir)
    except Exception:
        msg.verbose('could not remove directory [%s]' % tmpdir)
        pass

    if retval:
        signame = None
        if retval < 0: # signal?
            import signal
            for name, val in vars(signal).items():
                if len(name) > 3 and name[:3] == 'SIG' and name[3] != '_':
                    if val == -retval:
                        signame = name
                        break
        if signame:
            raise waflib.Errors.WafError(
                "Command %s terminated with signal %s." % (shell_cmd, signame))
        else:
            raise waflib.Errors.WafError(
                "Command %s exited with code %i" % (shell_cmd, retval))
    return retval

### ---------------------------------------------------------------------------
import waflib.Build
import waflib.Scripting
import waflib.Utils

class DumpEnvCmdContext(waflib.Build.BuildContext):
    """print the runtime environment in a json format"""
    cmd = 'dump-env'

    def execute_build(self):
        self.logger = msg

        lvl = msg.log.level
        if lvl < msg.logging.ERROR:
            msg.log.setLevel(msg.logging.ERROR)
            pass
        try:
            ret = super(DumpEnvCmdContext, self).execute_build()
        finally:
            msg.log.setLevel(lvl)

        py_exe = self.env.PYTHON
        if isinstance(py_exe, (list, tuple)):
            if len(py_exe) > 0: py_exe = str(py_exe[0])
            else: py_exe = "python"
            pass
        if py_exe == "": py_exe = "python"

        # get the runtime...
        env = _hwaf_get_runtime_env(self)

        import json
        import sys

        sys.stdout.write("%s\n" % json.dumps(env))
        sys.stdout.flush()
        return 0
    pass # RunCmdContext

## EOF ##
