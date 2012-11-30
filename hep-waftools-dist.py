# -*- python -*-

# stdlib imports
import os
import os.path as osp
import shutil
import sys

# waf imports ---
import waflib.Options
import waflib.Utils
import waflib.Logs as msg
import waflib.Build
import waflib.Context
from waflib.Configure import conf

_heptooldir = osp.dirname(osp.abspath(__file__))


def options(ctx):
    grp = ctx.add_option_group('bdist-rpm options')
    grp.add_option(
        "--rpm-pkg-ver",
        default=None,
        help="Sets the version of the RPM package",
        )
    grp.add_option(
        "--rpm-pkg-rev",
        default=None,
        help="Sets the revision of the RPM package",
        )
    grp.add_option(
        "--rpm-pkg-name",
        default=None,
        help="Sets the name of the RPM package",
        )
    grp.add_option(
        "--rpm-pkg-url",
        default=None,
        help="Sets the url of the RPM package home",
        )
    grp.add_option(
        "--rpm-pkg-cfg",
        default=None,
        help="Configure options to pass to the RPM configure/make/make-install step",
        )
    return

def configure(ctx):
    ctx.env.HEPWAF_BDIST_APPNAME = getattr(waflib.Context.g_module, "APPNAME", "noname")
    ctx.env.HEPWAF_BDIST_VERSION = getattr(waflib.Context.g_module, "VERSION", "0.0.1")
    return

### ---------------------------------------------------------------------------
g_rpm_spec_tmpl = '''\
%%define        __spec_install_post %%{nil}
%%define          debug_package %%{nil}
%%define        __os_install_post %%{_dbpath}/brp-compress
%%define _topdir   %(HEPWAF_BDIST_RPMBUILDROOT)s/rpmbuild
%%define _tmppath  %%{_topdir}/tmp
%%define _hepwaf_topdir %(PREFIX)s

Summary: hepwaf generated RPM for %(HEPWAF_BDIST_APPNAME)s
Name: %(RPM_PKG_NAME)s
Version: %(RPM_PKG_VER)s
Release: %(RPM_PKG_REV)s
License: BSD
Group: Science
SOURCE0 : %%{name}-%%{version}.tar.gz
URL: %(HEPWAF_BDIST_URL)s

BuildRoot: %%{_tmppath}/%%{name}-%%{version}-%%{release}-root

%%description
%%{summary}

%%prep
%%setup -q

%%build
./waf \
  configure \
  --prefix=%(PREFIX)s \
  --destdir=%%{buildroot} \
  %(RPM_PKG_CFG)s \
  build
  
%%install
rm -rf %%{buildroot}
mkdir -p  %%{buildroot}
./waf install --destdir=%%{buildroot}

%%clean
rm -rf %%{buildroot}


%%files
%%defattr(-,root,root,-)
%%{_hepwaf_topdir}/*

'''

### ---------------------------------------------------------------------------
class BdistRpmCmd(waflib.Configure.ConfigurationContext):
    cmd = 'bdist-rpm'

    def init_dirs(self, *k, **kw):
        super(BdistRpmCmd, self).init_dirs(*k, **kw)
        self.tmp = self.bldnode.make_node('bdist_rpm_tmp_dir')
        try:
            shutil.rmtree(self.tmp.abspath())
        except:
            pass
        if os.path.exists(self.tmp.abspath()):
            self.fatal('Could not remove the temporary directory %r' % self.tmp)
        self.tmp.mkdir()

        self.rpmbuildroot = self.tmp.make_node('rpmbuild')
        self.rpmbuildroot.mkdir()
        for d in 'RPMS SRPMS BUILD SOURCES SPECS tmp'.split():
            self.rpmbuildroot.make_node(d).mkdir()
            pass
        self.options.destdir = self.tmp.abspath()

    def execute(self, *k, **kw):
        # make sure we start from fresh...
        waflib.Context.create_context('clean').execute()
        ###
        
        back = self.options.destdir
        try:     super(BdistRpmCmd, self).execute(*k, **kw)
        finally: self.options.destdir = back

        self.find_program(
            "rpmbuild",
            var='RPMBUILD',
            mandatory=True,
            )
        pkg_ver = self.options.rpm_pkg_ver
        if not pkg_ver:
            pkg_ver = getattr(waflib.Context.g_module, "VERSION", "0.0.1")
            pass
        self.env.RPM_PKG_VER = pkg_ver

        pkg_rev = self.options.rpm_pkg_rev
        if not pkg_rev:
            pkg_rev = "1"
            pass
        self.env.RPM_PKG_REV = pkg_rev

        pkg_name = self.options.rpm_pkg_name
        if not pkg_name:
            pkg_name = getattr(waflib.Context.g_module, "APPNAME", "noname")
            pass
        self.env.RPM_PKG_NAME = pkg_name

        pkg_url = self.options.rpm_pkg_url
        if not pkg_url:
            pkg_url = "http://cern.ch"
            pass
        self.env.HEPWAF_BDIST_URL = pkg_url

        pkg_cfg = self.options.rpm_pkg_cfg
        if not pkg_cfg:
            pkg_cfg = ""
            pass
        self.env.RPM_PKG_CFG = pkg_cfg
        
        self.env.HEPWAF_BDIST_RPMBUILDROOT = self.tmp.abspath()

        for k in dict(self.env).keys():
            if k.startswith(('RPM','HEPWAF_')):
                self.declare_runtime_env(k)
                pass
            pass


        self.start_msg("building rpm package")
        rpm_name = "%s-%s-%s" % (self.env.RPM_PKG_NAME,
                                 self.env.RPM_PKG_VER,
                                 self.env.RPM_PKG_REV)
        self.end_msg(rpm_name)

        from waflib import Scripting
        ctx = Scripting.Dist()
        ctx.base_name = '%s-%s' % (self.env.RPM_PKG_NAME,
                                   self.env.RPM_PKG_VER,)
        ctx.arch_name = '%s-%s.tar.gz' % (self.env.RPM_PKG_NAME,
                                          self.env.RPM_PKG_VER,)
        ctx.algo = 'tar.gz'
        ctx.execute()

        # copy the tarball to SOURCES
        src_arch = self.path.find_node(ctx.arch_name)
        rpm_arch = self.rpmbuildroot.find_node('SOURCES').make_node(ctx.arch_name)
        shutil.copy(src=src_arch.abspath(),
                    dst=rpm_arch.abspath())

        # create spec-file
        spec = self.rpmbuildroot.find_node('SPECS').make_node(
            self.env.RPM_PKG_NAME+".spec")

        spec.write(g_rpm_spec_tmpl % dict(self.env))

        env = self._get_env_for_subproc()
        cmd = [self.env.RPMBUILD, '-ba', spec.path_from(self.rpmbuildroot)]

        try:
            rc=self.cmd_and_log(
                cmd,
                stdout=sys.stdout,
                stderr=sys.stderr,
                cwd=self.rpmbuildroot.abspath(),
                output=waflib.Context.BOTH,
                env=env,
                )
        except Exception as e:
            self.fatal(e.stdout)
            pass

        # fetch back the RPM
        arch = 'x86_64'
        if self.is_32b():arch = 'i686'
        rpm_name = "%s.%s.rpm" % (rpm_name, arch)
        rpm = self.rpmbuildroot.find_node('RPMS').find_node(arch).find_node(rpm_name)
        dst_rpm = self.path.make_node(rpm_name)
        shutil.copy(src=rpm.abspath(),
                    dst=dst_rpm.abspath())
        
        shutil.rmtree(self.tmp.abspath())
        msg.info('New RPM created: %s' % dst_rpm)
        
        return rc
        
    pass
waflib.Context.g_module.__dict__['_bdist_rpm'] = BdistRpmCmd


### ---------------------------------------------------------------------------
class BDist(waflib.Build.InstallContext):
    '''creates an archive containing the project binaries'''

    cmd = 'bdist'

    def init_dirs(self, *k, **kw):
        super(BDist, self).init_dirs(*k, **kw)
        self.tmp = self.bldnode.make_node('bdist_tmp_dir')
        try:
            shutil.rmtree(self.tmp.abspath())
        except:
            pass
        if os.path.exists(self.tmp.abspath()):
            self.fatal('Could not remove the temporary directory %r' % self.tmp)
        self.tmp.mkdir()
        self.options.destdir = self.tmp.abspath()

    def execute(self, *k, **kw):
        back = self.options.destdir
        try:
            super(BDist, self).execute(*k, **kw)
        finally:
            self.options.destdir = back

        files = self.tmp.ant_glob('**')

        # we could mess with multiple inheritance but this is probably unnecessary
        from waflib import Scripting
        ctx = Scripting.Dist()
        project_name = self.env.HEPWAF_BDIST_APPNAME
        variant = self.env.CMTCFG
        version = self.env.HEPWAF_BDIST_VERSION
        ctx.arch_name = '%s-%s-%s.tar.gz' % (project_name,
                                             variant,
                                             version)
        ctx.algo = 'tar.gz'
        ctx.files = files
        ctx.tar_prefix = ''
        ctx.base_path = self.tmp
        ctx.archive()

        shutil.rmtree(self.tmp.abspath())
        return
    pass # class BDist
waflib.Context.g_module.__dict__['_bdist'] = BDist

