#!/usr/bin/env python
'''

This module provides the decompose() function.

'''
import os

def parse_val(val, orig = None):
    '''Parse and apply a value setting command: val = <action>:value to
    original value <orig>.  <action> can be "append", "prepend" or
    "set".  If no "<action>:" is given, "set:" is assumed.
    '''
    if val.startswith('append'):
        val = val[len('append'):]
        delim = val[0]
        val = val[1:]
        if not orig: return val
        orig = orig.split(delim)
        while val in orig:
            orig.remove(val)
        return delim.join(orig + [val])

    if val.startswith('prepend'):
        val = val[len('prepend'):]
        delim = val[0]
        val = val[1:]
        if not orig: return val
        orig = orig.split(delim)
        while val in orig:
            orig.remove(val)
        return delim.join([val] + orig)

    if val.startswith('set'):
        val = val[len('set')+1]
    return val

def set_environment(environ, pkg, prefix = 'export_'):
    '''Apply any environment variable settings implied by
    <prefix>_VARIABLE to the <environ> dictionary
    '''
    for k,v in pkg.items():
        if not k.startswith(prefix):
            continue
        var = k.split('_',1)[1]
        old = environ.get(var)
        val = parse_val(v, old)
        environ[var] = val
        #print 'Setting %s=%s (was:%s)' % (var, val, old)


def packages_in_group(pkglist, group_name):
    '''
    Given a list of all packages, return a list of those in the named group.
    '''
    ret = []
    for pkg in pkglist:
        if pkg.get('group') == group_name:
            ret.append(pkg)
    return ret

def resolve_packages(all_packages, desclist):
    '''Resolve packages given a description list.  Each element of the
    list is like <what>:<name> where <what> is "group" or "package"
    and <name> is the group or package name.  The list can be in the
    form of a sequence of descriptors or as a single comma-separated
    string.
    '''
    if not desclist:
        return list()

    if isinstance(desclist, type("")):
        desclist = [x.strip() for x in desclist.split(',')]
    ret = []
    for req in desclist:
        what,name = req.split(':')
        if what == 'package':
            pkg = all_packages[name]
            ret.append(pkg)
            continue
        if what == 'group':
            for pkg in packages_in_group(all_packages.values(), name):
                if pkg in ret:
                    continue
                ret.append(pkg)
        else:
            raise ValueError('Unknown descriptor: "%s:%s"' % (what, name))
        continue
    return ret


def make_environ(pkg, all_packages):
    '''Add an environ to a waf <env> for given package.  The environ
    starts with os.environ, adds any settings specified by
    'export_VARIABLE' in any dependent packages or groups of packages
    indicated by an "environment" package variable and finally by any
    specified by "buildenv_VARIABLE" in the package itself.
    '''
    environ = dict(os.environ)
    for other_pkg in resolve_packages(all_packages, pkg.get('environment')):
        set_environment(environ, other_pkg)
    set_environment(environ, pkg, prefix='buildenv_')
    return environ
        
def decompose(cfg, suite):
    '''Decompose suite into packages and groups of packages.  

    For every group in the suite there is one added to the waf <cfg> context.  

    Every package has an env of the same name added to <cfg> which
    contains variables defined either through its "environment"
    variable or through any variables with names beginning with
    "buildenv_".

    '''
    base_env = cfg.env

    # fixme: should use ordered dict
    gl,gd = [], {}
    pl,pd = [], {}
    for group in suite['groups']:
        group_name = group['group']
        gl.append(group_name)
        gd[group_name] = group
        for package in group['packages']:
            package_name = package['package']
            pl.append(package_name)
            pd[package_name] = package

    base_env.orch_group_list = gl
    base_env.orch_group_dict = gd
    base_env.orch_package_list = pl
    base_env.orch_package_dict = pd

    for pkg_name, pkg in pd.items():
        cfg.setenv(pkg_name, base_env.derive())
        environ = make_environ(pkg, pd)
        cfg.env.environ = environ


    return

