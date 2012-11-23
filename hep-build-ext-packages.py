# -*- python -*-

"""
Obtain packages, unpack them in a location, and add associated uselib variables
(CFLAGS_pkgname, LIBPATH_pkgname, etc).

The default is use a Dependencies.txt file in the source directory.

This is a work in progress.

Usage:

def options(opt):
    opt.load('package')

def configure(conf):
    conf.load_packages()
"""
import os
import os.path as osp
import shlex

import waflib.Build
from waflib.Configure import conf
import waflib.Logs as msg
import waflib.Task
import waflib.TaskGen
import waflib.Utils

try:    from urllib import request
except: from urllib import urlopen
else:   urlopen = request.urlopen

# hepwaf imports
import waflib.extras.waffle_utils as waffle_utils
import waflib.extras.waffle_subprocess as subprocess

CACHEVAR = 'WAFCACHE_PACKAGE'

#
_heptooldir = osp.dirname(osp.abspath(__file__))

def configure(ctx):
    ctx.load('hep-waftools-base', tooldir=_heptooldir)
    pass

@conf
def get_package_cache_dir(self):
    cache = None
    if CACHEVAR in conf.environ:
        cache = conf.environ[CACHEVAR]
        cache = self.root.make_node(cache)
    elif self.env[CACHEVAR]:
        cache = self.env[CACHEVAR]
        cache = self.root.make_node(cache)
    else:
        cache = self.srcnode.make_node('.wafcache_package')
    cache.mkdir()
    return cache

@conf
def download_archive(self, src, dst):
    for x in self.env.PACKAGE_REPO:
        url = '/'.join((x, src))
        try:
            web = urlopen(url)
            try:
                if web.getcode() != 200:
                    continue
            except AttributeError:
                pass
        except Exception:
            # on python3 urlopen throws an exception
            # python 2.3 does not have getcode and throws an exception to fail
            continue
        else:
            tmp = self.root.make_node(dst)
            tmp.write(web.read(),'wb')
            msg.warn('Downloaded %s from %s' % (tmp.abspath(), url))
            break
    else:
        self.fatal('Could not get the package %s' % src)

@conf
def load_packages(self):
    cache = self.get_package_cache_dir()
    # read the dependencies, get the archives, ..


@conf
def declare_build_external(
    self, name,
    prefix = None, # <name>-build-ext
    tmp_dir= None, # <prefix>/tmp
    stamp_dir= None, # <prefix>/<name>-stamp
    download_dir= None, # <prefix>/src
    source_dir= None, # <prefix>/src/<name>
    build_dir= None, # <prefix>/src/<name>-build
    install_dir= None, # env.PREFIX
    # --- switches ---
    build_in_source = False,
    # --- input location(s) ---
    url = None, # ex: file:///foo or http://bar
    url_md5 = None,
    svn_repository = None,
    svn_revision = None,
    cvs_repository = None,
    cvs_revision = None,
    # --- build steps ---
    patch_cmd = None, # ex: 'patch -p0 foo.patch'
    configure_cmd = None, # ex: 'configure --prefix=${PREFIX}'
    build_cmd = None, # ex: 'make'
    install_cmd = None, # ex: 'make install DESTDIR=${BUILD_INSTALL_AREA}
    # --- build environment ---
    env = None,
    os_env_keys = None,
    shell = False,
    ):
    # set defaults
    if prefix is None:
        prefix = self.bldnode.make_node('%s-build-ext' % name)
    else:
        prefix = self.bldnode.make_node(prefix)
    if tmp_dir is None:
        tmp_dir = prefix.make_node('tmp')
    else:
        tmp_dir = self.bldnode.make_node(tmp_dir)
    
    if stamp_dir is None:
        stamp_dir = prefix.make_node('%s-stamp' % name)
    else:
        stamp_dir = self.bldnode.make_node(stamp_dir)

    if download_dir is None:
        download_dir = prefix.make_node('src')
    else:
        download_dir = self.bldnode.make_node(download_dir)

    if source_dir is None:
        source_dir = prefix.make_node(name)
    else:
        source_dir = self.bldnode.make_node(source_dir)

    if build_dir is None:
        if build_in_source:
            build_dir = source_dir
        else:
            build_dir = prefix.make_node('%s-build' % name)
    else:
        build_dir = self.bldnode.make_node(build_dir)

    if install_dir is None:
        install_dir = prefix.make_node('%s-install' % name)
        #install_dir = self.env.INSTALL_AREA
    else:
        install_dir = prefix.make_node(install_dir)
        #install_dir = self.root.make_node(install_dir)

    if os_env_keys is None:
        os_env_keys = []
    os_env_keys += self.env.HEPWAF_RUNTIME_ENVVARS[:]

    for d in (tmp_dir,
              stamp_dir,
              download_dir,
              source_dir,
              build_dir,
              install_dir,
              ):
        d.mkdir()
        pass

    if (url is None and
        svn_repository is None and
        cvs_repository is None):
        self.fatal('You need to give "declare_build_external" an url')
        pass

    def _get_cmd(cmd):
        if isinstance(cmd, str):
            cmd = shlex.split(cmd)
            pass
        return [waflib.Utils.subst_vars(c, self.env) for c in cmd]

    ## stamp files
    unpack_stamp = stamp_dir.make_node('000-unpack.stamp')
    patch_stamp = stamp_dir.make_node('001-patch.stamp')
    configure_stamp = stamp_dir.make_node('002-configure.stamp')
    make_stamp = stamp_dir.make_node('003-make.stamp')
    make_install_stamp = stamp_dir.make_node('004-make_install.stamp')

    ## log-files
    unpack_log = tmp_dir.make_node('000-unpack.log')
    patch_log = tmp_dir.make_node('001-patch.log')
    configure_log = tmp_dir.make_node('002-configure.log')
    make_log = tmp_dir.make_node('003-make.log')
    make_install_log = tmp_dir.make_node('004-make_install.log')

    ## env...
    self.env['EXT_BUNDLED_%s_ROOT'%name.upper()] = install_dir.abspath()
    if env is None:
        env = waffle_utils._get_env_for_subproc(self, os_env_keys)
    else:
        # do not modify user's env...
        env = dict(env)
        senv = waffle_utils._get_env_for_subproc(self, os_env_keys)
        for k in ('CXXFLAGS',
                  'CCFLAGS',
                  'CFLAGS',
                  'CPPFLAGS',
                  'LINKFLAGS',
                  'CC',
                  'CXX',
                  ):
            env[k] = senv[k]
            pass
        pass
    for k in env.keys():
        if not k in os_env_keys:
            del env[k]
    env['EXT_BUNDLED_%s_ROOT'%name.upper()] = install_dir.abspath()
        
    for k,v in env.iteritems():
        if not isinstance(v, str):
            raise ValueError("invalid env.var: ${%s} = %r" % (k,v))
        
    ## retrieve the sources...
    pkg_src = None
    if not (url is None):
        url = waflib.Utils.subst_vars(url, self.env)
        pkg_src = download_dir.make_node(os.path.basename(url))
        if not os.path.exists(pkg_src.abspath()):
            msg.info("[%s] retrieving sources..." % name)
            self.download_archive(src=url, dst=pkg_src.abspath())
            if url_md5:
                import hashlib
                hasher = hashlib.md5()
                hasher.update(pkg_src.read('rb'))
                md5 = hasher.hexdigest()
                if url_md5 != md5:
                    self.fatal("[%s] invalid MD5 checksum:\nref: %s\nnew: %s"
                               % (name, url_md5, md5))
        pass


    ## unpack the sources...
    # find the correct unpacker...
    if not os.path.exists(unpack_stamp.abspath()):
        msg.info('[%s] unpacking...' % name)
        unpack_dir = tmp_dir.make_node("unpack-dir")
        unpack_dir.mkdir()
        import tarfile
        import zipfile
        if tarfile.is_tarfile(pkg_src.abspath()):
            o = tarfile.open(pkg_src.abspath())
            o.extractall(unpack_dir.abspath())
            o.close()
        elif zipfile.is_zipfile(pkg_src.abspath()):
            o = zipfile.open(pkg_src.abspath())
            o.extractall(unpack_dir.abspath())
            o.close()
        else:
            msg.info('[%s] file [%s] is not a recognized archive format'
                      % (name, pkg_src.abspath()))
            pass
        unpack_content = unpack_dir.ant_glob("*", dir=True)
        import shutil
        shutil.rmtree(path=source_dir.abspath(),
                      ignore_errors=True)
        if (len(unpack_content) == 1 and 
            os.path.isdir(unpack_content[0].abspath())):
            shutil.move(src=unpack_content[0].abspath(),
                        dst=source_dir.abspath())
        else:
            shutil.move(src=unpack_dir.abspath(),
                        dst=source_dir.abspath())
        shutil.rmtree(path=unpack_dir.abspath(),
                      ignore_errors=True)
        unpack_stamp.write('')

    ## real build...
    if patch_cmd:
        cmd = _get_cmd(patch_cmd)
        if not os.path.exists(patch_stamp.abspath()):
            cwd=build_dir.abspath()
            msg.info('[%s] patching...' % name)
            fout = open(patch_log.abspath(), 'w')
            fout.write('++ cd %s\n' % cwd)
            fout.write('++ %s\n' % cmd)
            fout.flush()
            sc = subprocess.call(
                waflib.Utils.to_list(cmd),
                env=env,
                stdout=fout,
                stderr=fout,
                cwd=cwd
                )
            if sc != 0:
                self.fatal("failed to patch [%s]\nlook into [%s]" %
                           (name, fout.name))
            patch_stamp.write('')

    if not os.path.exists(configure_stamp.abspath()):
        msg.info('[%s] configuring...' % name)
        cmd = _get_cmd(configure_cmd)
        cwd=build_dir.abspath()
        fout = open(configure_log.abspath(), 'w')
        fout.write('++ cd %s\n' % cwd)
        fout.write('++ %s\n' % cmd)
        fout.flush()
        if isinstance(cmd, str):
            cmd = waflib.Utils.to_list(cmd)
            pass
        sc = subprocess.call(
            cmd,
            env=env,
            stdout=fout,
            stderr=fout,
            cwd=cwd
            )
        if sc != 0:
            self.fatal("failed to configure [%s]\nlook into [%s]" %
                       (name, fout.name))
        configure_stamp.write('')

    self.env['EXT_PKG_BUILD_%s' % name] = {
        'build': {
            'cmd': _get_cmd(build_cmd),
            'env': env,
            'cwd': build_dir.abspath(),
            'stdout': make_log.abspath(),
            'shell': shell,
            'stamp': make_stamp.abspath(),
            },
        'install': {
            'cmd': _get_cmd(install_cmd),
            'env': env,
            'cwd': build_dir.abspath(),
            'stdout': make_install_log.abspath(),
            'shell': shell,
            'stamp': make_install_stamp.abspath(),
            },
        }

    if 0 and not os.path.exists(make_stamp.abspath()):
        msg.info('[%s] building...' % name)
        cmd = _get_cmd(build_cmd)
        cwd=build_dir.abspath()
        fout = open(make_log.abspath(), 'w')
        fout.write('++ cd %s\n' % cwd)
        fout.write('++ %s\n' % cmd)
        fout.flush()
        sc = subprocess.call(
            waflib.Utils.to_list(cmd),
            env=env,
            stdout=fout,
            stderr=fout,
            cwd=cwd,
            shell=shell
            )
        if sc != 0:
            self.fatal("failed to build [%s]\nlook into [%s]" %
                       (name, fout.name))
        make_stamp.write('')

    if 0 and not os.path.exists(make_install_stamp.abspath()):
        msg.info('[%s] installing...' % name)
        cmd = _get_cmd(install_cmd)
        cwd=build_dir.abspath()
        fout = open(make_install_log.abspath(), 'w')
        fout.write('++ cd %s\n' % cwd)
        fout.write('++ %s\n' % cmd)
        fout.flush()
        sc = subprocess.call(
            waflib.Utils.to_list(cmd),
            env=env,
            stdout=fout,
            stderr=fout,
            cwd=cwd
            )
        if sc != 0:
            self.fatal("failed to install [%s]\nlook into [%s]" %
                       (name, fout.name))
        make_install_stamp.write('')

    # create signatures for all nodes under ${EXT_BUNDLED_<name>_ROOT}
    outputs = install_dir.ant_glob('**/*')
    for o in outputs:
        #print("-- %s" % o.abspath())
        o.sig = waflib.Utils.h_file(o.abspath())

    return

### ---
#@waflib.TaskGen.feature('build_external_pkg')
@waflib.TaskGen.extension('.extpkg')
@waflib.TaskGen.after('process_source')
def schedule_build_external_pkg(self, *k, **kwd):
    bld_node = self.bld.bldnode
    out_node = bld_node.make_node("%s-build-ext" % self.name)
    tmp_node = out_node.make_node("tmp")
    outputs = []
    stamp_node = out_node.make_node("%s-stamp"%self.name)
    stamp_files = [
        "003-make.stamp",
        ]
    if self.bld.cmd == 'install':
        stamp_files += ["004-make_install.stamp",]
        pass
    for o in stamp_files:
        o = stamp_node.make_node(o)
        #o.sig = waflib.Utils.h_file(o.abspath())
        outputs += [o]
        #try:    os.remove(o.abspath())
        #except: pass
        pass
    tsk = self.create_task('build_external_pkg', self.source, outputs)
    #self.source += tsk.outputs
    #merge_dsomap_hook(self, out_node).set_run_after(tsk)
    return

class build_external_pkg(waflib.Task.Task):
    vars = ['DEFINES', 'CPPFLAGS', 'INCLUDES', 'PREFIX', 'CC', 'CXX']
    color= 'BLUE'
    run_str = 'hep-waf-bld-ext-pkg ${SRC[0].name} -o ${TGT}'
    ext_in  = ['.extpkg']
    shell = False
    reentrant = False
    #after = ['cxxshlib', 'cxxprogram', 'symlink_tsk']

    def exec_command(self, cmd, **kw):
        ctx = self.generator.bld
        tsk_name = self.generator.name
        ext_env = ctx.env['EXT_PKG_BUILD_%s' % tsk_name][ctx.cmd]
        if ctx.cmd == 'build':
            msg.info('[%s] building...' % tsk_name)
            pass
        
        cmd = ext_env['cmd']
        env= ctx._get_env_for_subproc()
        cwd= ext_env['cwd']
        fout = open(ext_env['stdout'], 'w')
        fout.write('++ cd %s\n' % cwd)
        fout.write('++ %s\n' % cmd)
        fout.flush()
        sc = subprocess.call(
            waflib.Utils.to_list(cmd),
            env=env,
            stdout=fout,
            stderr=fout,
            cwd=cwd,
            shell=ext_env['shell']
            )
        if sc != 0:
            ctx.fatal("failed to %s [%s]\nlook into [%s]" %
                      (ctx.cmd, name, fout.name))
            pass
        stamp = open(ext_env['stamp'], 'w')
        stamp.write('')
        stamp.flush()
        return sc

    def runnable_status(self):
        status = waflib.Task.Task.runnable_status(self)
        if status == waflib.Task.ASK_LATER:
            return status
        
        for out_node in self.outputs:
            try:
                os.stat(out_node.abspath())
            except:
                return waflib.Task.RUN_ME
        return status
    pass
