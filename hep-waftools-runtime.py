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
import waflib.Utils

_heptooldir = osp.dirname(osp.abspath(__file__))

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
        ret = hwaf_run_cmd_with_runtime_env(self, args)
        return ret
    pass # RunCmdContext

def hwaf_run_cmd_with_runtime_env(ctx, cmds):
    # make sure we build first"
    # waflib.Scripting.run_command('install')
    
    import os
    import tempfile
    import textwrap

    #env = ctx.env
    cwd = os.getcwd()
    root = os.path.realpath(ctx.options.prefix)
    # FIXME: we should use the *local* install-area to be
    #        able to test the runtime w/o requiring an actual install!!
    root = os.path.realpath(ctx.env['INSTALL_AREA'])
    bindir = os.path.join(root, 'bin')
    libdir = os.path.join(root, 'lib')
    pydir  = os.path.join(root, 'python')

    # get the runtime...
    env = _get_runtime_env(ctx)

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
            for name, val in vars(signal).iteritems():
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
    root = os.path.realpath(ctx.env['INSTALL_AREA'])
    bindir = os.path.join(root, 'bin')
    libdir = os.path.join(root, 'lib')
    pydir  = os.path.join(root, 'python')

    # get the runtime...
    env = _get_runtime_env(ctx)


    ## handle the shell flavours...
    if waffle_utils._is_linux(ctx):
        ppid = os.getppid()
        shell = os.path.realpath('/proc/%d/exe' % ppid)
    elif waffle_utils._is_darwin(ctx):
        ppid = os.getppid()
        shell = os.popen('ps -p %d -o %s | tail -1' % (ppid, "command")).read()
        shell = shell.strip()
        if shell.startswith('-'):
            shell = shell[1:]
    elif waffle_utils._is_windows(ctx):
        ## FIXME: ???
        shell = None
    else:
        shell = None
        pass

    # catch-all
    if not shell or "(deleted)" in shell:
        # fallback on the *login* shell
        shell = os.environ.get("SHELL", "/bin/sh")

    tmpdir = tempfile.mkdtemp(prefix='waffle-env-')
    dotrc = None
    dotrc_fname = None
    shell_cmd = [shell,]
    msg.info("---> shell: %s" % shell)

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

    # FIXME: this should probably be done elsewhere (and better)
    #env['ROOTSYS'] = os.getenv('ROOTSYS', ctx.env.ROOTSYS)
    if ctx.env['BUNDLED_ROOT']:
        rootsys_setup = textwrap.dedent('''
        pushd ${ROOTSYS}
        echo ":: sourcing \${ROOTSYS}/bin/thisroot.sh..."
        source ./bin/thisroot.sh
        popd
        ''')

    else:
        rootsys_setup = ''
        pass
    ###


    dotrc = open(dotrc_fname, 'w')
    dotrc.write(textwrap.dedent(
        '''
        ## automatically generated by waffle-shell
        echo ":::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::"
        echo ":: launching a sub-shell with the correct mana environment..."
        echo ":: sourcing ${HOME}/%(dotrc_fname)s..."
        source ${HOME}/%(dotrc_fname)s
        echo ":: sourcing ${HOME}/%(dotrc_fname)s... [done]"

        # adjust env. variables
        export PATH=%(waffle_path)s
        export LD_LIBRARY_PATH=%(waffle_ld_library_path)s
        export DYLD_LIBRARY_PATH=%(waffle_dyld_library_path)s

        # for ROOT
        ROOTSYS=%(rootsys)s
        %(rootsys_setup)s

        # setup PYTHONPATH *after* ROOT so "we" win
        export PYTHONPATH=%(waffle_pythonpath)s

        # env. variables for athena
        JOBOPTSEARCHPATH=%(waffle_joboptsearchpath)s
        DATAPATH=.:%(waffle_datapath)s

        # customize PS1 so we know we are in a waffle subshell
        export PS1="[waf] ${PS1}"

        echo ":: mana environment... [setup]"
        echo ":: hit ^D or exit to go back to the parent shell"
        echo ":::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::"
        ''' % {
            'dotrc_fname' : os.path.basename(dotrc_fname),
            'waffle_path': env['PATH'],
            'waffle_ld_library_path': env['LD_LIBRARY_PATH'],
            'waffle_dyld_library_path': env['DYLD_LIBRARY_PATH'],
            'waffle_pythonpath': env['PYTHONPATH'],
            'waffle_joboptsearchpath': env['JOBOPTSEARCHPATH'],
            'waffle_datapath': env['DATAPATH'],
            'rootsys':  env['ROOTSYS'],
            'rootsys_setup': rootsys_setup,
            }
        ))
    dotrc.flush()
    dotrc.close()

    for k in env:
        v = env[k]
        if not isinstance(v, str):
            ctx.fatal('env[%s]=%r (%s)' % (k,v,type(v)))
            

    retval = subprocess.Popen(
        shell_cmd,
        env=env,
        cwd=os.getcwd()
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
            for name, val in vars(signal).iteritems():
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

## EOF ##
