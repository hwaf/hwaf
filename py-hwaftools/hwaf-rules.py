# -*- python -*-

# stdlib imports
import os
import os.path as osp
import sys

# waf imports ---
import waflib.Utils
import waflib.Logs as msg
import waflib.Configure
import waflib.Build
import waflib.Task
import waflib.Tools.ccroot
from waflib.Configure import conf
from waflib.TaskGen import feature, before_method, after_method, extension, after

_heptooldir = osp.dirname(osp.abspath(__file__))
# add this directory to sys.path to ease the loading of other hepwaf tools
if not _heptooldir in sys.path: sys.path.append(_heptooldir)

### ---------------------------------------------------------------------------
class symlink_tsk(waflib.Task.Task):
    """
    A task to install symlinks of binaries and libraries under the *build*
    install-area (to not require shaggy RPATH)
    this is needed e.g. for genconf and gencliddb.
    """
    color   = 'PINK'
    reentrant = True
    
    def run(self):
        import os
        try:
            os.remove(self.outputs[0].abspath())
        except OSError:
            pass
        return os.symlink(self.inputs[0].abspath(),
                          self.outputs[0].abspath())


@feature('symlink_tsk')
@after_method('apply_link')
def add_install_copy(self):
    link_tsk = getattr(self, 'link_task', None)
    if not link_tsk:
        return
    link_cls_name = self.link_task.__class__.__name__
    # FIXME: is there an API for this ?
    if link_cls_name.endswith('lib'):
        outdir = self.bld.path.make_node('.install_area').make_node('lib')
    else:
        outdir = self.bld.path.make_node('.install_area').make_node('bin')
    link_outputs = waflib.Utils.to_list(self.link_task.outputs)
    for out in link_outputs:
        if isinstance(out, str):
            n = out
        else:
            n = out.name
        out_sym = outdir.find_or_declare(n)
        #print("===> ", self.target, link_cls_name, out_sym.abspath())
        tsk = self.create_task('symlink_tsk',
                               out,
                               out_sym)
        self.source += tsk.outputs
        pass
    return

### ---------------------------------------------------------------------------
@before_method('process_source')
@feature('hwaf_install_headers')
def hwaf_install_headers(self):
    """
    A task to install header files.
    This assumes a package has one of the following layout:
     <pkgroot>
       /<pkgname>/hdr1.h
       /src

     <pkgroot>
       /inc/<pkgname>/hdr1.h
       /src
    """
    # extract package name
    pkgdir = self.path.abspath()
    pkgname = self.bld.hwaf_pkg_name(pkgdir)
    b_pkgname = osp.basename(pkgname)
    if not hasattr(self, 'export_includes'):
        return
    
    include_dir = getattr(self, 'include_dir', b_pkgname)
    inc_node = self.path.find_dir(include_dir)
    if not inc_node:
        self.bld.fatal('[%s]: could not find package headers' % (pkgname,))
        pass

    cwd = getattr(self, 'cwd', None)
    relative_trick = getattr(self, 'relative_trick', True)
    postpone = getattr(self, "postpone", False)
    
    if isinstance(cwd, (list, tuple)): cwd = cwd[0]
    if isinstance(cwd, type("")): cwd = self.path.find_dir(cwd)
    if cwd is None:               cwd = self.path

    includes = inc_node.ant_glob('**/*', dir=False)
    self.bld.install_files(
        '${INSTALL_AREA}/include',
        includes, 
        relative_trick=relative_trick,
        cwd=cwd,
        postpone=postpone,
        )

    incpath = waflib.Utils.subst_vars('${INSTALL_AREA}/include',self.bld.env)
    self.bld.env.append_unique('INCLUDES_%s' % self.name,
                               [incpath,inc_node.parent.abspath()])
    return

### -----------------------------------------------------------------------------
import waflib.Build
class InstallContext(waflib.Build.InstallContext):
    '''
    InstallContext class to be less verbose by default
    '''
    def __init__(self, **kw):
        super(InstallContext, self).__init__(**kw)
        return

    def execute_build(self):
        self.logger = msg
        lvl = msg.log.level
        if not msg.verbose:
            if lvl < msg.logging.ERROR:
                msg.log.setLevel(msg.logging.ERROR)
                pass
        try:
            ret = super(InstallContext, self).execute_build()
        finally:
            msg.log.setLevel(lvl)
        return ret
    pass # class InstallContext

### -----------------------------------------------------------------------------
import waflib.Build
class UninstallContext(waflib.Build.UninstallContext):
    '''
    UninstallContext class to be less verbose by default
    '''
    def __init__(self, **kw):
        super(UninstallContext, self).__init__(**kw)
        return

    def execute_build(self):
        self.logger = msg
        lvl = msg.log.level
        if not msg.verbose:
            if lvl < msg.logging.ERROR:
                msg.log.setLevel(msg.logging.ERROR)
        try:
            ret = super(UninstallContext, self).execute_build()
        finally:
            msg.log.setLevel(lvl)
        return ret
    pass # class UninstallContext

### ---------------------------------------------------------------------------
import os, sys
from waflib.TaskGen import feature, after_method
from waflib import Utils, Task, Logs, Options

@feature('hwaf_utest')
@after('symlink_tsk')
def make_test(self):
    """Create the unit test task. There can be only one unit test task by task generator."""
    if getattr(self, 'link_task', None):
        self.create_task('hwaf_utest', self.link_task.outputs)

g_testlock = Utils.threading.Lock()

class hwaf_utest(Task.Task):
    """
    Execute a unit test.

    ctx(
        features='test cxx cxxprogram',
        source='foo.cxx',
        target='app',
        ut_cwd=None,           # optional dir for running test
        ut_args=['--verbose'], # optional additional arguments to test-binary
        ut_rc=0,               # optional expected return code
    )
    """
    color = 'CYAN'
    after = ['vnum', 'inst', 'symlink_tsk']
    vars = []
    
    
    def runnable_status(self):
        """
        Always execute the task if `waf --alltests` was used or no
                tests if ``waf --notests`` was used
        """
        if getattr(Options.options, 'no_tests', True):
            return Task.SKIP_ME

        if not self.generator.bld.cmd in ('build', 'check'):
            return Task.SKIP_ME
        
        ret = super(hwaf_utest, self).runnable_status()
        #print("%s: ret=%s" % (self.inputs[0].name, ret))
        if ret in (Task.SKIP_ME, Task.RUN_ME):
            if getattr(Options.options, 'all_tests', False):
                depends = waflib.Utils.to_list(getattr(self.generator, 'depends_on', []))
                #print("%s: deps=%s" % (self.inputs[0].name, depends))
                if depends:
                    results = getattr(self.generator.bld, 'hwaf_utest_results', [])
                    dep = 0
                    for tup in results:
                        fname = tup[0]
                        fname = osp.basename(fname)
                        #print("%s: fname=%s ?" % (self.inputs[0].name, fname))
                        if fname in depends:
                            #print("%s: fname=%s YES!" % (self.inputs[0].name, fname))
                            dep += 1
                    if dep == len(depends):
                        #print("%s: ALL DEPS OK!" % (self.inputs[0].name,))
                        return Task.RUN_ME
                    #print("%s: RUN LATER" % (self.inputs[0].name,))
                    return Task.ASK_LATER
                else:
                    return Task.RUN_ME
        return ret

    def run(self):
        """
        Execute the test. The execution is always successful, but the results
        are stored on ``self.generator.bld.hwaf_utest_results`` for postprocessing.
        """

        filename = self.inputs[0].abspath()
        self.ut_exec = getattr(self.generator, 'ut_exec', [filename])
        if getattr(self.generator, 'ut_fun', None):
            # FIXME waf 1.8 - add a return statement here?
            self.generator.ut_fun(self)

        try:
            fu = getattr(self.generator.bld, 'all_test_paths')
        except AttributeError:
            # this operation may be performed by at most #maxjobs
            fu = os.environ.copy()

            lst = []
            for g in self.generator.bld.groups:
                for tg in g:
                    if getattr(tg, 'link_task', None):
                        s = tg.link_task.outputs[0].parent.abspath()
                        if s not in lst:
                            lst.append(s)

            def add_path(dct, path, var):
                dct[var] = os.pathsep.join(Utils.to_list(path) + [os.environ.get(var, '')])

            if Utils.is_win32:
                add_path(fu, lst, 'PATH')
            elif Utils.unversioned_sys_platform() == 'darwin':
                add_path(fu, lst, 'DYLD_LIBRARY_PATH')
                add_path(fu, lst, 'LD_LIBRARY_PATH')
            else:
                add_path(fu, lst, 'LD_LIBRARY_PATH')
            self.generator.bld.all_test_paths = fu
            pass

        self.ut_exec = Utils.to_list(self.ut_exec)
        
        cwd = getattr(self.generator, 'ut_cwd', None) or self.inputs[0].parent.abspath()

        args = Utils.to_list(getattr(self.generator, 'ut_args', []))
        if args:
            self.ut_exec.extend(args)
        
        testcmd = getattr(Options.options, 'testcmd', False)
        if testcmd:
            self.ut_exec = (testcmd % self.ut_exec[0]).split(' ')

        returncode = getattr(self.generator, 'ut_rc', 0)
        if isinstance(returncode, (list,tuple)):
            returncode = int(returncode[0])
        
        #print(">>>> running %s..." % self.ut_exec[0])
        proc = Utils.subprocess.Popen(
            self.ut_exec,
            cwd=cwd,
            env=fu,
            stderr=Utils.subprocess.PIPE,
            stdout=Utils.subprocess.PIPE
            )
        (stdout, stderr) = proc.communicate()

        tup = (filename, proc.returncode, stdout, stderr, returncode)
        self.generator.utest_result = tup

        g_testlock.acquire()
        try:
            bld = self.generator.bld
            Logs.debug("ut: %r", tup)
            try:
                bld.hwaf_utest_results.append(tup)
            except AttributeError:
                bld.hwaf_utest_results = [tup]
        finally:
            #print(">>>> running %s... [done]" % self.ut_exec[0])
            g_testlock.release()

@waflib.Configure.conf
def hwaf_utest_summary(bld, *k, **kwargs):
    """
    Display an execution summary::

        def build(bld):
            bld(features='cxx cxxprogram test', source='main.c', target='app')
            bld.add_post_fun(hwaf_utest_summary)
    """
    lst = getattr(bld, 'hwaf_utest_results', [])
    if lst:
        Logs.pprint('CYAN', '='*80)
        Logs.pprint('CYAN', 'unit-tests execution summary')

        total = len(lst)
        tfail = len([x for x in lst if x[1] != x[4]])
        val = 100 * (total - tfail) / (1.0 * total)
        Logs.pprint('CYAN', 'test report %3.0f%% success' % val)
        
        Logs.pprint('CYAN', '  tests that pass %d/%d' % (total-tfail, total))
        for (f, code, out, err, exp_rc) in lst:
            if code == exp_rc:
                Logs.pprint('CYAN', '    %s' % f)
                pass
            pass

        Logs.pprint('CYAN', '  tests that fail %d/%d' % (tfail, total))
        for (f, code, out, err, exp_rc) in lst:
            if code != exp_rc:
                Logs.pprint('CYAN', '    %s (err=%d, exp=%d)' % (f,code, exp_rc))
                pass
            pass
        Logs.pprint('CYAN', '='*80)
        pass
    return

@waflib.Configure.conf
def hwaf_utest_set_exit_code(bld, *k):
    """
    If any of the tests fail waf will exit with that exit code.
    This is useful if you have an automated build system which need
    to report on errors from the tests.
    You may use it like this:
    
    def build(bld):
        bld(features='cxx cxxprogram test', source='main.c', target='app')
        bld.add_post_fun(hwaf_unit_set_exit_code)
    """
    lst = getattr(bld, 'hwaf_utest_results', [])
    if not lst:
        return

    msg = []
    for (f, code, out, err, exp_rc) in lst:
        if code != exp_rc:
            msg.append('=== %s === (err=%d expected=%d)' % (f,code, exp_rc))
            if out: msg.append('stdout:%s%s' % (os.linesep, out.decode('utf-8')))
            if err: msg.append('stderr:%s%s' % (os.linesep, err.decode('utf-8')))
            pass
        pass
    
    if msg: bld.fatal(os.linesep.join(msg))
    return

def options(opt):
    """
    Provide the ``--alltests``, ``--notests`` and ``--testcmd`` command-line options.
    """
    opt.add_option(
        '--notests',
        action='store_true',
        default=False,
        help='Exec no unit tests',
        dest='no_tests')

    opt.add_option(
        '--alltests',
        action='store_true',
        default=False,
        help='Exec all unit tests',
        dest='all_tests')

    opt.add_option(
        '--testcmd',
        action='store',
        default=False,
        help = 'Run the unit tests using the test-cmd string'
               ' example "--test-cmd="valgrind --error-exitcode=1'
               ' %s" to run under valgrind', dest='testcmd')

## EOF ##
