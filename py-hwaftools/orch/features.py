#!/usr/bin/env python
# encoding: utf-8

## stdlib imports
import os.path as osp
from pprint import PrettyPrinter
pp = PrettyPrinter(indent=2)
try:    from urllib import request
except: from urllib import urlopen
else:   urlopen = request.urlopen

## waflib imports
from waflib import TaskGen
import waflib.Errors
import waflib.Logs as msg

def _worch_exec_command(task, cmd, **kw):
    '''
    helper function to:
     - run a command
     - log stderr and stdout into worch_<taskname>.log.txt
     - printout the content of that file when the command fails
    '''
    msg.debug('orch: %s...' % task.name)
    cwd = getattr(task, 'cwd', task.generator.bld.path.abspath())
    flog = open(osp.join(cwd, "worch_%s.log.txt" % task.name), 'w')
    cmd_dict = dict(kw)
    cmd_dict.update({
        'cwd': cwd,
        'stdout': flog,
        'stderr': flog,
        })
    try:
        o = task.exec_command(cmd, **cmd_dict)
    except KeyboardInterrupt:
        raise
    finally:
        flog.close()
    if msg.verbose and o == 0 and 'orch' in msg.zones:
        with open(flog.name) as f:
            msg.pprint('NORMAL','orch: %s (%s)\n%s' % (task.name, flog.name, ''.join(f.readlines())))
            pass
        pass
    if o != 0:
        msg.error('orch: %s (%s)\n%s' % (task.name, flog.name, ''.join(open(flog.name).readlines())))
    return o
    
class PackageFeatureInfo(object):
    '''
    Give convenient access to all info about a package for features.

    Also sets the contexts group and env to the ones for the package.
    '''

    def __init__(self, package_name, feature_name, ctx, defaults):
        self.package_name = package_name
        self.feature_name = feature_name
        self.pkgdata = ctx.all_envs[''].orch_package_dict[package_name]
        self.env = ctx.all_envs[package_name]
        environ = self.env.munged_env
        self.env.env = environ

        self.ctx = ctx

        # fixme: this is confusing
        self.defs = defaults
        f = dict(self.defs)
        f.update(dict(self.ctx.env))
        f.update(self.pkgdata)
        self._data = f

        group = self.get_var('group')
        self.ctx.set_group(group)

        msg.debug(
            'orch: Feature: "{feature}" for package "{package}/{version}" in group "{group}"'.
            format(feature = feature_name, **self.pkgdata))

    def __call__(self, name):
        return self.get_var(name)

    def format(self, string, **extra):
        d = dict(self._data)
        d.update(extra)
        return string.format(**d)

    def get_var(self, name):
        val = self.pkgdata.get(name, self.defs.get(name))
        if not val: return
        return self.check_return(name, self.format(val))

    def get_node(self, name, dir_node = None):
        var = self.get_var(name)
        if not var: 
            return self.check_return('var:'+name)
        if dir_node:
            return self.check_return('node:%s/%s'%(name,var), dir_node.make_node(var))
        path = self.ctx.bldnode
        if var.startswith('/'):
            path = self.ctx.root
        return self.check_return('node:%s/%s'%(name,var),  path.make_node(var))

    def check_return(self, name, ret=None):
        if ret: 
            # try:
            #     full = ret.abspath()
            # except AttributeError:
            #     full = ''
            #msg.debug('orch: Variable for {package}/{version}: {varname} = {value} ({full})'.\
            #    format(varname=name, value=ret, full=full, **self._data))
            return ret
        raise ValueError(
            'Failed to get "%s" for package "%s"' % 
            (name, self.pkgdata['package'])
            )

    def get_deps(self, step):
        deps = self.pkgdata.get('depends')
        if not deps: return list()
        mine = []
        for dep in [x.strip() for x in deps.split(',')]:
            if ':' in dep:
                dep = dep.split(':',1)
                if dep[0] == step:
                    mine.append(dep[1])
                    continue
            else:
                mine.append(dep)
        if mine:
            msg.debug(
                self.format('orch: Package {package} step "{step}" depends: "{dep}"',
                            step=step,dep=','.join(mine))
                )
        return mine

@TaskGen.feature('dumpenv')
def feature_dumpenv(self):
    '''
    Dump the environment
    '''
    pfi = PackageFeatureInfo(self.package_name, 'dumpenv', self.bld, dict())

    self.bld(name = pfi.format('{package}_dumpenv'),
             rule = "/bin/env | sort",
             env = pfi.env)


def get_unpacker(filename, dirname):
    if filename.endswith('.zip'): 
        return 'unzip -d %s %s' % (dirname, filename)
    
    text2flags = {'.tar.gz':'xzf', '.tgz':'xzf', '.tar.bz2':'xjf', '.tar':'xf' }
    for ext, flags in text2flags.items():
        if filename.endswith(ext):
            return 'tar -C %s -%s %s' % (dirname, flags, filename)
    return 'tar -C %s -xf %s' % (dirname, filename)

tarball_requirements = {
    'source_urlfile': '{package}-{version}.url',
    'source_url': None,
    'source_url_checksum': None, # md5:xxxxx, sha224:xxxx, sha256:xxxx, ...
    'srcpkg_ext': 'tar.gz',
    'source_package': '{package}-{version}.{srcpkg_ext}',
    'download_dir': 'downloads',
    'download_target': '{download_dir}/{source_package}',
    'source_dir': 'sources',
    'source_unpacked': '{package}-{version}',
    'unpacked_target': 'configure',
}


@TaskGen.feature('tarball')
def feature_tarball(self):
    '''
    Handle a tarball source.  Implements steps seturl, download and unpack
    '''
    pfi = PackageFeatureInfo(self.package_name, 'tarball', self.bld, tarball_requirements)


    f_urlfile = pfi.get_node('source_urlfile')
    d_download = pfi.get_node('download_dir')
    f_tarball = pfi.get_node('source_package', d_download)

    d_source = pfi.get_node('source_dir')
    d_unpacked = pfi.get_node('source_unpacked', d_source)
    f_unpack = pfi.get_node('unpacked_target', d_unpacked)

    self.bld(name = pfi.format('{package}_seturl'),
             rule = "echo %s > ${TGT}" % pfi('source_url'), 
             update_outputs = True,
             target = f_urlfile,
             depends_on = pfi.get_deps('seturl'),
             env = pfi.env)

    def dl_task(task):
        src = task.inputs[0]
        tgt = task.outputs[0]
        url = src.read().strip()
        try:
            web = urlopen(url)
            tgt.write(web.read(),'wb')
        except Exception:
            import traceback
            traceback.print_exc()
            self.bld.fatal("[%s] problem downloading [%s]" % (pfi.format('{package}_download'), url))

        checksum = pfi.get_var('source_url_checksum')
        if not checksum:
            return
        hasher_name, ref = checksum.split(":")
        import hashlib
        # FIXME: check the hasher method exists. check for typos.
        hasher = getattr(hashlib, hasher_name)()
        hasher.update(tgt.read('rb'))
        data= hasher.hexdigest()
        if data != ref:
            self.bld.fatal(
                "[%s] invalid MD5 checksum:\nref: %s\nnew: %s"
                % (pfi.format('{package}_download'), ref, data))
        return

    self.bld(name = pfi.format('{package}_download'),
             rule = dl_task,
             source = f_urlfile, 
             target = f_tarball,
             depends_on = pfi.get_deps('download'),
             env = pfi.env)

    self.bld(name = pfi.format('{package}_unpack'), 
             rule = get_unpacker(f_tarball.abspath(), f_unpack.parent.parent.abspath()),
             source = f_tarball, target = f_unpack,
             depends_on = pfi.get_deps('unpack'),
             env = pfi.env)

    return

patch_requirements = {
    'patch_urlfile': '{package}-{version}.patch.url',
    'patch_url': None,
    'patch_ext': 'patch', # or diff
    'patch_package': '{package}-{version}.{patch_ext}',
    'patch_cmd': 'patch',
    'patch_cmd_options': '-i',
    'patch_target': '{package}-{version}.{patch_ext}.applied',
}


@TaskGen.feature('patch')
def feature_patch(self):
    '''
    Apply a patch on the unpacked sources.
    '''
    reqs = dict(patch_requirements, **tarball_requirements)
    pfi = PackageFeatureInfo(self.package_name, 'patch', self.bld, reqs)

    if not pfi('patch_url'):
        return

    f_urlfile = pfi.get_node('patch_urlfile')
    d_patch = pfi.get_node('source_dir')
    f_patch = pfi.get_node('patch_package', d_patch)
    f_applied = pfi.get_node('patch_target', d_patch)

    d_source = pfi.get_node('source_dir')
    d_unpacked = pfi.get_node('source_unpacked', d_source)
    f_unpack = pfi.get_node('unpacked_target', d_unpacked)
    
    self.bld(name = pfi.format('{package}_urlpatch'),
             rule = "echo %s > ${TGT}" % pfi('patch_url'), 
             update_outputs = True,
             source = f_unpack,
             target = f_urlfile,
             depends_on = pfi.get_deps('patch') + [pfi.format('{package}_unpack')],
             env = pfi.env)

    def dl_task(task):
        src = task.inputs[0]
        tgt = task.outputs[0]
        url = src.read().strip()
        try:
            web = urlopen(url)
            tgt.write(web.read(),'wb')
        except Exception:
            import traceback
            traceback.print_exc()
            self.bld.fatal("[%s] problem downloading [%s]" % (pfi.format('{package}_dlpatch'), url))

    self.bld(name = pfi.format('{package}_dlpatch'),
             rule = dl_task,
             source = f_urlfile,
             target = f_patch,
             depends_on = pfi.get_deps('dlpatch'),
             env = pfi.env)

    def apply_patch(task):
        src = task.inputs[0].abspath()
        tgt = task.outputs[0].abspath()
        cmd = "%s %s %s" % (
            pfi.get_var('patch_cmd'),
            pfi.get_var('patch_cmd_options'),
            src,
            )
        o = _worch_exec_command(task, cmd)
        if o != 0:
            return o
        cmd = "touch %s" % tgt
        o = task.exec_command(cmd)
        return o
    
    step_name = pfi.format('{package}_patch')
    self.bld(name = step_name, 
             rule = apply_patch,
             source = f_patch,
             target = f_applied,
             cwd = pfi.get_node('source_dir').abspath(),
             depends_on = pfi.get_deps('patch'),
             env = pfi.env)

    # make sure {package}_prepare will wait for us to be done.
    tsk = self.bld.get_tgen_by_name(pfi.format('{package}_prepare'))
    tsk.depends_on.append(step_name)
    return

git_requirements = {
    'git_urlfile': '{package}.git.url',
    'git_url': None,
    'git_cmd': 'git clone',
    'git_cmd_options': '',
    'source_dir': 'sources',
    'source_unpacked': '{package}-git',
    'unpacked_target': 'configure',
}


@TaskGen.feature('git')
def feature_git(self):
    '''
    Checkout a git repository.  Implements steps seturl and checkout.
    '''
    pfi = PackageFeatureInfo(self.package_name, 'git', self.bld, git_requirements)


    if not pfi('git_url'):
        self.fatal(
            "git feature enabled for package [%s] but not 'git_url'" %
            self.package_name,
            )
        return
    
    f_urlfile = pfi.get_node('git_urlfile')

    d_source = pfi.get_node('source_dir')
    d_unpacked = pfi.get_node('source_unpacked', d_source)
    f_unpack = pfi.get_node('unpacked_target', d_unpacked)

    def create_urlfile(task):
        tgt = task.outputs[0]
        tgt.write("%s %s -b %s %s %s" % (
            pfi.get_var('git_cmd'),
            pfi.get_var('git_cmd_options') or '',
            pfi.get_var('version'),
            pfi.get_var('git_url'),
            d_unpacked.abspath(),
            ))
        return 0
    
    self.bld(name = pfi.format('{package}_seturl'),
             rule = create_urlfile,
             update_outputs = True,
             target = f_urlfile,
             depends_on = pfi.get_deps('seturl'),
             env = pfi.env)

    def checkout_task(task):
        src = task.inputs[0]
        tgt = task.outputs[0]
        cmd = "%s" % (src.read(),)
        return _worch_exec_command(task, cmd)

    self.bld(name = pfi.format('{package}_checkout'),
             rule = checkout_task,
             source = f_urlfile,
             target = f_unpack,
             depends_on = pfi.get_deps('checkout'),
             env = pfi.env)

    return

hg_requirements = {
    'hg_urlfile': '{package}.hg.url',
    'hg_url': None,
    'hg_cmd': 'hg clone',
    'hg_cmd_options': '',
    'source_dir': 'sources',
    'source_unpacked': '{package}-hg',
    'unpacked_target': 'configure',
}


@TaskGen.feature('hg')
def feature_hg(self):
    '''
    Checkout a mercurial repository.  Implements steps seturl and checkout.
    '''
    pfi = PackageFeatureInfo(self.package_name, 'hg', self.bld, hg_requirements)


    if not pfi('hg_url'):
        self.fatal(
            "hg feature enabled for package [%s] but not 'hg_url'" %
            self.package_name,
            )
        return
    
    f_urlfile = pfi.get_node('hg_urlfile')

    d_source = pfi.get_node('source_dir')
    d_unpacked = pfi.get_node('source_unpacked', d_source)
    f_unpack = pfi.get_node('unpacked_target', d_unpacked)

    def create_urlfile(task):
        tgt = task.outputs[0]
        tgt.write("%s %s -b %s %s %s" % (
            pfi.get_var('hg_cmd'),
            pfi.get_var('hg_cmd_options') or '',
            pfi.get_var('version'),
            pfi.get_var('hg_url'),
            d_unpacked.abspath(),
            ))
        return 0
    
    self.bld(name = pfi.format('{package}_seturl'),
             rule = create_urlfile,
             update_outputs = True,
             target = f_urlfile,
             depends_on = pfi.get_deps('seturl'),
             env = pfi.env)

    def checkout_task(task):
        src = task.inputs[0]
        tgt = task.outputs[0]
        cmd = "%s" % (src.read(),)
        return _worch_exec_command(task, cmd)

    self.bld(name = pfi.format('{package}_checkout'),
             rule = checkout_task,
             source = f_urlfile,
             target = f_unpack,
             depends_on = pfi.get_deps('checkout'),
             env = pfi.env)

    return

svn_requirements = {
    'svn_urlfile': '{package}.svn.url',
    'svn_url': None,
    'svn_cmd': 'svn checkout',
    'svn_cmd_options': '',
    'source_dir': 'sources',
    'source_unpacked': '{package}-svn',
    'unpacked_target': 'configure',
}


@TaskGen.feature('svn')
def feature_svn(self):
    '''
    Checkout a subversion repository.  Implements steps seturl and checkout.
    '''
    pfi = PackageFeatureInfo(self.package_name, 'svn', self.bld, svn_requirements)


    if not pfi('svn_url'):
        self.fatal(
            "svn feature enabled for package [%s] but not 'svn_url'" %
            self.package_name,
            )
        return
    
    f_urlfile = pfi.get_node('svn_urlfile')

    d_source = pfi.get_node('source_dir')
    d_unpacked = pfi.get_node('source_unpacked', d_source)
    f_unpack = pfi.get_node('unpacked_target', d_unpacked)

    def create_urlfile(task):
        tgt = task.outputs[0]
        tgt.write("%s %s %s %s" % (
            pfi.get_var('svn_cmd'),
            pfi.get_var('svn_cmd_options') or '',
            pfi.get_var('svn_url'),
            d_unpacked.abspath(),
            ))
        return 0
    
    self.bld(name = pfi.format('{package}_seturl'),
             rule = create_urlfile,
             update_outputs = True,
             target = f_urlfile,
             depends_on = pfi.get_deps('seturl'),
             env = pfi.env)

    def checkout_task(task):
        src = task.inputs[0]
        tgt = task.outputs[0]
        cmd = "%s" % (src.read(),)
        return _worch_exec_command(task, cmd)

    self.bld(name = pfi.format('{package}_checkout'),
             rule = checkout_task,
             source = f_urlfile,
             target = f_unpack,
             depends_on = pfi.get_deps('checkout'),
             env = pfi.env)

    return

autoconf_requirements = {
    'source_dir': 'sources',
    'source_unpacked': '{package}-{version}',
    'prepare_script': 'configure',
    'prepare_script_options': '--prefix={install_dir}',
    'prepare_target': 'config.status',
    'build_dir': 'builds/{package}-{version}',
    'build_cmd': 'make',
    'build_cmd_options': None,
    'build_target': None,
    'install_dir': '{PREFIX}',
    'install_cmd': 'make install',
    'install_cmd_options': None,
    'install_target': None,
}

@TaskGen.feature('autoconf')
def feature_autoconf(self):
    pfi = PackageFeatureInfo(self.package_name, 'autoconf', self.bld, autoconf_requirements)

    d_source = pfi.get_node('source_dir')
    d_unpacked = pfi.get_node('source_unpacked', d_source)
    f_prepare = pfi.get_node('prepare_script',d_unpacked)
    d_build = pfi.get_node('build_dir')
    f_prepare_result = pfi.get_node('prepare_target', d_build)
    f_build_result = pfi.get_node('build_target', d_build)

    d_prefix = pfi.get_node('install_dir')
    f_install_result = pfi.get_node('install_target', d_prefix)

    def prepare_task(task):
        src = task.inputs[0]
        tgt = task.outputs[0]
        
        cmd = "%s %s" % (src.abspath(), pfi.get_var('prepare_script_options'))
        return _worch_exec_command(task, cmd)
        
        
    self.bld(name = pfi.format('{package}_prepare'),
             rule = prepare_task,
             source = f_prepare,
             target = f_prepare_result,
             cwd = d_build.abspath(),
             depends_on = pfi.get_deps('prepare'),
             env = pfi.env)

    def build_task(task):
        src = task.inputs[0]
        tgt = task.outputs[0]
        cmd = "%s %s" % (
                 pfi.get_var('build_cmd'),
                 pfi.get_var('build_cmd_options') or '',
            )
        return _worch_exec_command(task, cmd)
        
    self.bld(name = pfi.format('{package}_build'),
             rule = build_task,
             source = f_prepare_result,
             target = f_build_result,
             cwd = d_build.abspath(),
             depends_on = pfi.get_deps('build'),
             env = pfi.env)

    def install_task(task):
        src = task.inputs[0]
        tgt = task.outputs[0]
        cmd = "%s %s" % (
                 pfi.get_var('install_cmd'),
                 pfi.get_var('install_cmd_options') or '',
            )
        return _worch_exec_command(task, cmd)
        
    self.bld(name = pfi.format('{package}_install'),
             rule = install_task,
             source = f_build_result,
             target = f_install_result,
             cwd = d_build.abspath(),
             depends_on = pfi.get_deps('install'),
             env = pfi.env)

    # testing
    # if pd['package'] != 'cmake':
    #     self.bld(name = '{package}_which'.format(**pd),
    #              rule = 'which cmake', env=pfi.env,
    #              depends_on = 'cmake_install')


    return

