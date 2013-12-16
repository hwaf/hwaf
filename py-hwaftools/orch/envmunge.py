#!/usr/bin/env python
'''

This module primarily provides the decompose() function.

'''

from . import mungers


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

        
def make_envmungers(pkg, all_packages):
    '''Make a environment munger that will apply the export_VARIABLE
    settings from all dependency packages indicated by the
    "environment" package variable (and the export_VAR from 'depends'
    packages) and any specified by buildenv_VARIABLE in the package
    itself.  Note, that the export_* variables from a given package
    are explicitly NOT applied to the package itself.
    '''
    autoenv = []
    deps = pkg.get('depends') or []
    if isinstance(deps, type("")): deps = deps.split()
    
    for dep in deps:
        _, step = dep.split(':')
        what = step.split('_')[0]
        if what in all_packages:
            #print 'autoenv: package: "%s"' % what
            autoenv.append('package:%s' % what)
        else: # FIXME: assume this is a group, then.
            #print 'autoenv: group: "%s"' % what
            autoenv.append('group:%s' % what)

    if pkg.get('environment'):
        en = pkg.get('environment')
        #print 'autoenv: environment: "%s"' % en
        autoenv.extend([x.strip() for x in en.split(',')])
        
    ret = list()
    for other_pkg in resolve_packages(all_packages, autoenv):
        ret += mungers.construct('export_', **other_pkg)

    ret += mungers.construct('buildenv_', **pkg)

    # Do NOT append export_ mungers for the current pkg.

    return ret

def decompose(cfg, suite):
    '''Decompose suite into packages and groups of packages.  

    For every group in the suite there is one added to the waf <cfg> context.  

    Every package has an env of the same name added to <cfg> which
    contains variables defined either through its "environment"
    variable or through any variables with names beginning with
    "buildenv_".

    The waf env is given a "munged_env" element which holds the result
    of any environment munging applied to the current process
    environment (os.environ).
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

        mlist = make_envmungers(pkg, pd)
        environ = cfg.env.env or dict()
        menv = mungers.apply(mlist, **environ)

        new_env = base_env.derive()
        new_env.munged_env = menv
        cfg.setenv(pkg_name, new_env)

    return

