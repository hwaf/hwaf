#!/usr/bin/env python
import waflib.Logs as msg
import os.path as osp
from . import requirements as reqmod
from orch import deconf
from orch import pkgconf


class PackageFeatureInfo(object):
    '''
    Give convenient access to all info about a package for features.

    Also sets the contexts group and env to the ones for the package.
    '''

    step_cwd = dict(patch = 'source_dir',
                    prepare = 'build_dir',
                    build = 'build_dir',
                    install = 'build_dir',
                    )

    def __init__(self, feature_name, ctx, **pkgcfg):

        self._data = pkgcfg
        self.feature_name = feature_name
        self.package_name = pkgcfg['package']
        self._env = ctx.all_envs[self.package_name]
        self._env.env = self._env.munged_env
        self._ctx = ctx
        self._inserted_dependencies = list() # list of (before, after) tuples
        
        #self.dump()
        msg.debug(            
            self.format(
                'orch: Feature: "{feature}" for package "{package}/{version}" in group "{group}"',
                feature = feature_name))

    def dump(self):
        msg.debug('orch: PFI:', self.package_name, self.feature_name, len(self._data), sorted(self._data.items()))
        for k,v in sorted(self._data.items()):
            if v is None:
                msg.debug('orch: PFI: %s: %s: "%s" is None' % (self.package_name, self.feature_name, k))
                continue
            n = getattr(self, k)
            p = ''
            r = reqmod.pool.get(k)
            if r and r.typecode in ['d','f']:
                p = n.abspath()
                pass
            val = ' value is okay'
            if v is None:
                val = ' value is None'
            elif '{' in v:
                val = ' value is unformed'
            msg.debug('orch: PFI: %s: %s: "%s" = "%s" = "%s" %s%s' % (self.package_name, self.feature_name, k,v,n,p, val))


    def __call__(self, name, dir = None):
        if dir and isinstance(dir, type('')):
            dir = self.node(dir)
        return self.node(name, dir)

    def __getattr__(self, name):
        val = self._data[name]
        if val is None:
            raise ValueError(
                '"%s" is None for feature: "%s", package: "%s"' % 
                (name, self.feature_name, self.package_name)
                )
        req = reqmod.pool.get(name)
        if req and req.typecode.lower() in ['d','f']:
            parent = None
            if req.relative:
                parent = self.node(self.format(req.relative))
            return self.node(val, parent)
        return val

    def node(self, path, parent_node=None):
        if not parent_node:
            if path.startswith('/'):
                parent_node = self._ctx.root
            else:
                parent_node = self._ctx.bldnode
        return parent_node.make_node(path)

    def task(self, name, **kwds):
        task_name = self.format('{package}_%s'%name)
        kwds.setdefault('env', self._env)
        deps = set()
        if 'depends_on' in kwds:
            depon = kwds.pop('depends_on')
            if isinstance(depon, type('')):
                depon = [depon]
            deps.update(depon)
        deps.update(self._get_deps(name))
        for dep in deps:
            self.dependency(dep, task_name)

        if not 'cwd' in kwds:
            dirname = self.step_cwd.get(name)
            if dirname:
                dirnode = getattr(self, dirname)
                path = dirnode.abspath()
                msg.debug('orch: setting cwd for %s to %s' % (task_name, path))
                kwds['cwd'] = path
        msg.debug('orch: register task: "%s", "%s"' % (task_name, kwds.get('source')))
        self._ctx(name = task_name, **kwds)
        return


    def register_dependencies(self):
        '''
        Call after all task() has been called for whole suite.
        '''
        for before, after in self._inserted_dependencies:
            msg.debug('orch: dependency: %s --> %s' % (before, after))
            tsk = self._ctx.get_tgen_by_name(after)
            if not hasattr(tsk,'depends_on'):
                tsk.depends_on = list()
            tsk.depends_on.append(before)


    def dependency(self, before, after):
        '''
        Insert step name <before> before step named <after>
        '''
        self._inserted_dependencies.append((before, after))
        #tsk = self._ctx.get_tgen_by_name()
        #tsk.depends_on.append()
        return
        
    def format(self, string, **extra):
        d = dict(self._data)
        d.update(extra)
        return string.format(**d)

    def debug(self, string, *a, **k):
        msg.debug(self.format(string), *a, **k)
    def info(self, string, *a, **k):
        msg.info(self.format(string), *a, **k)
    def warn(self, string, *a, **k):
        msg.warn(self.format(string), *a, **k)
    def error(self, string, *a, **k):
        msg.error(self.format(string), *a, **k)


    def _get_deps(self, step):
        deps = self._data.get('depends')
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

registered_func = dict()        # feature name -> function
registered_config = dict()  # feature name -> configuration dictionary
def feature(feature_name, **feature_config):
    def wrapper(feat_func):
        def wrap(bld, package_config):
            pfi = PackageFeatureInfo(feature_name, bld, **package_config)
            feat_func(pfi)
            return pfi
        registered_func[feature_name] = wrap
        registered_config[feature_name] = feature_config
        return wrap
    return wrapper
