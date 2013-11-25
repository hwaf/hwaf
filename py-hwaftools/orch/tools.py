#!/usr/bin/env python
'''
Main entry to worch from a waf wscript file.

Use the following in the options(), configure() and build() waf wscript methods:

    ctx.load('orch.tools', tooldir='.')

'''

def options(opt):
    opt.add_option('--orch-config', action = 'store', default = 'orch.cfg',
                   help='Give an orchestration configuration file.')
    opt.add_option('--orch-start', action = 'store', default = 'start',
                   help='Set the section to start the orchestration')

def configure(cfg):
    import orch.configure
    orch.configure.configure(cfg)

def build(bld):
    import orch.build
    orch.build.build(bld)
    

# the stuff below is for augmenting waf

import time
from orch.wafutil import exec_command
from orch.util import string2list

default_step_cwd = dict(
    download = '{download_dir}',
    unpack = '{source_dir}',
    patch = '{source_dir}',
    prepare = '{build_dir}',
    build = '{build_dir}',
    install = '{build_dir}',
)

# Main interface to worch configuration items
class WorchConfig(object):
    def __init__(self, **pkgcfg):
        self._config = pkgcfg
    def __getattr__(self, name):
        return self._config[name]

    def get(self, name, default = None):
        return self._config.get(name,default)

    def format(self, string, **kwds):
        '''
        Return a string formatted with kwds and configuration items
        '''
        d = dict(self._config, **kwds)
        return string.format(**d)

    def depends_step(self, step):
        '''
        Return a list of steps that this step depends on
        '''
        d = self._config.get('depends')
        if not d: return list()
        ds = [x[1] for x in [s.split(':') for s in string2list(d)] if x[0] == step]
        return ds
        
    def dependencies(self):
        '''
        Return all dependencies set via "depends" configuration items 
        return list of tuples: (mystep, package, package_step)
        eg: ('prepare', 'gcc', 'install')
        '''
        ret = list()
        try:
            deps = getattr(self, 'depends', None)
        except KeyError:
            return list()
        for dep in string2list(deps):
            mystep, other = dep.split(':')
            pkg,pkg_step = other.split('_',1)
            ret.append((mystep, pkg, pkg_step))
        return ret

    def exports(self):
        '''
        Return all environment settings via export_* configuration items
        return list of tuples: (variable, value, operator) for exports
        eg: ('PATH', '/blah/blah', 'prepend')
        '''
        ret = list()
        for key,val in self._config.items():
            if not key.startswith('export_'):
                continue
            var = key[len('export_'):]
            oper = 'set'
            for maybe in ['prepend', 'append', 'set']:
                if val.startswith(maybe+':'):
                    oper = maybe
                    val = val[len(maybe)+1:]
            ret.append((var, val, oper))
        return ret



# Augment the task generator with worch-specific methods
from waflib.TaskGen import taskgen_method

@taskgen_method
def worch_hello(self):
    'Just testing'
    print ("%s" % self.worch.format('Hi from worch, my name is "{package}/{version}" and I am using "{dumpenv_cmd}" with extra {extra}', extra='spice'))
    print ('My bld.env: %s' % (self.bld.env.keys(),))
    print ('My all_envs: %s' % (sorted(self.bld.all_envs.keys()),))
    print ('My env: %s' % (self.env.keys(),))
    print ('My groups: %s' % (self.env['orch_group_dict'].keys(),))
    print ('My packages: %s' % (self.env['orch_package_list'],))
#    print ('My package dict: %s' % '\n'.join(['%s=%s' %kv for kv in sorted(self.bld.env['orch_package_dict'][self.worch.package].items())]))



@taskgen_method
def step(self, name, rule, **kwds):
    '''
    Make a worch installation step.  

    This invokes the build context on the rule with the following augmentations:

    - the given step name is prefixed with the package name
    - if the rule is a string (scriptlet) then the worch exec_command is used
    - successful execution of the rule leads to a worch control file being produced.
    '''
    step_name = '%s_%s' % (self.worch.package, name)

    # append control file as an additional output
    target = string2list(kwds.get('target', ''))
    if not isinstance(target, list):
        target = [target]
    cn = self.control_node(name)
    if not cn in target:
        target.append(cn)
    kwds['target'] = target
    
    kwds.setdefault('env', self.env)

    cwd = kwds.get('cwd')
    if not cwd:
        cwd = default_step_cwd.get(name)
    if cwd:
        cwd = self.worch.format(cwd)
        cwd = self.make_node(cwd)
        msg.debug('orch: using cwd for step "%s": %s' % (step_name, cwd.abspath()))
        kwds['cwd'] = cwd.abspath()


    depends = self.worch.depends_step(name)
    after = string2list(kwds.get('after',[])) + depends
    if after:
        kwds['after'] = after
        msg.debug('orch: run %s AFTER: %s' % (step_name, after))

    # functionalize scriptlet
    rulefun = rule
    if isinstance(rule, type('')):
        rulefun = lambda t: exec_command(t, rule)

    # curry the real rule function in order to write control file if successful
    def runit(t):
        rc = rulefun(t)
        if not rc:
            msg.debug('orch: successfully ran %s' % step_name)
            cn.write(time.asctime(time.localtime()) + '\n')
        return rc

    # msg.debug('orch: step "%s" with %s in %s\nsource=%s\ntarget=%s' % \
    #           (step_name, rulefun, cwd, kwds.get('source'), kwds.get('target')))

    # have to switch group each time as steps are called already asynchronously
    self.bld.set_group(self.worch.group)
    return self.bld(name=step_name, rule = runit, **kwds)
    
@taskgen_method
def control_node(self, step, package = None):
    '''
    Return a node for the control file given step of this package or optionally another package.
    '''
    if not package:
        package = self.worch.package
    filename = '%s_%s' % (package, step)
    path = self.worch.format('{control_dir}/{filename}', filename=filename)
    return self.path.find_or_declare(path)

@taskgen_method
def make_node(self, path, parent_node=None):
    if not parent_node:
        if path.startswith('/'):
            parent_node = self.bld.root
        else:
            parent_node = self.bld.bldnode
    return parent_node.make_node(path)


import waflib.Logs as msg
from waflib.Build import BuildContext
def worch_package(ctx, worch_config, *args, **kw):

    # transfer waf-specific keywords explicitly
    kw['name'] = worch_config['package']
    kw['features'] = ' '.join(string2list(worch_config['features']))
    kw['use'] = worch_config.get('use')

    # make the TaskGen object for the package
    worch=WorchConfig(**worch_config)
    tgen = ctx(*args, worch=worch, **kw)
    tgen.env = ctx.all_envs[worch.package]
    tgen.env.env = tgen.env.munged_env
    msg.debug('orch: package "%s" with features: %s' % \
              (kw['name'], ', '.join(kw['features'].split())))
    return tgen
BuildContext.worch_package = worch_package
del worch_package
