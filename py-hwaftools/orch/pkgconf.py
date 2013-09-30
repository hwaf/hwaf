#!/usr/bin/env python
'''
Package specific interpretation layered on deconf.
'''

import os
    
from . import deconf
from .util import check_output, CalledProcessError, update_if, string2list
from . import features as featmod

def ups_flavor():
    '''
    Ow, my balls.
    '''
    kern, host, rel, vend, mach = os.uname()
    if mach in ['x86_64','sun','ppc64']:
        mach = '64bit'
    else:
        mach = ''
    rel = '.'.join(rel.split('.')[:2])
    if 'darwin' in kern.lower():
        libc = rel # FIXME: is there something better on mac ?
    else:
        libc = check_output(['ldd','--version']).split(b'\n')[0].split()[-1]
    return '%s%s+%s-%s' % (kern, mach, rel, libc)

def ncpus():
    try:
        import psutil
        return psutil.NUM_CPUS
    except ImportError:
        pass

    try:
        import multiprocessing
        return multiprocessing.cpu_count()
    except ImportError:
        pass
    except NotImplementedError:
        pass

    return 1

def host_description():
    '''
    Return a dictionary of host description variables.
    '''
    ret = {}
    uname_fields = ['kernelname', 'hostname', 
                    'kernelversion', 'vendorstring', 'machine']
    uname = os.uname()
    for k,v in zip(uname_fields, uname):
        ret[k] = v
    platform = '{kernelname}-{machine}'.format(**ret)
    ret['platform'] = platform
    try:
        flavor = check_output(['ups','flavor'])
    except OSError:
        flavor = ups_flavor()
    ret['ups_flavor'] = flavor

    bits = '32'
    libbits = 'lib'
    if uname[-1] in ['x86_64']: # fixme: mac os x?
        bits = '64'
        libbits = 'lib64'
    ret['bits'] = bits
    ret['libbits'] = libbits
    ret['gcc_dumpversion'] = check_output(['gcc','-dumpversion']).strip()
    ret['gcc_dumpmachine'] = check_output(['gcc','-dumpmachine']).strip()
    try:
        ma = check_output(
            ['gcc','-print-multiarch'],    # debian-specific
            stderr=open('/dev/null', 'w')
            ).strip()
    except CalledProcessError:
        ma = ""
    ret['gcc_multiarch'] = ma
    if 'darwin' in ret['kernelname'].lower():
        libc_version = ret['kernelversion'] # FIXME: something better on Mac ?
    else:
        libc_version = check_output(['ldd','--version']).split(b'\n')[0].split()[-1]
    ret['libc_version'] = libc_version
    ret['NCPUS'] = ncpus()
        
    return ret


class PkgFormatter(object):
    def __init__(self, **kwds):
        self.vars = host_description()
        self.vars.update(kwds)

    def __call__(self, string, **kwds):
        if not string: return string
        tags = kwds.get('tags') or ''
        tags = [x.strip() for x in tags.split(',')]
        kwds.setdefault('tagsdashed',  '-'.join(tags))
        kwds.setdefault('tagsunderscore', '_'.join(tags))

        version = kwds.get('version')
        if version:
            kwds.setdefault('version_2digit', '.'.join(version.split('.')[:2]))
            kwds.setdefault('version_underscore', version.replace('.','_'))
            kwds.setdefault('version_dashed', version.replace('.','-'))
            kwds.setdefault('version_nodots', version.replace('.',''))
        vars = dict(self.vars)
        vars.update(kwds)
        ret = string.format(**vars)
        return ret

def fold_in_feature_requirements(suite, formatter = None, **kwds):
    # fold in feature defaults
    for group in suite['groups']:
        new_packages = list()
        for package in group['packages']:
            featlist = string2list(package.get('features'))
            featcfg = featmod.feature_requirements(featlist)
            package = update_if(featcfg, None, **package)            
            new_packages.append(package)
        group['packages'] = new_packages

    if not formatter:
        formatter = PkgFormatter()
    suite = deconf.format_any(suite, formatter=formatter, **kwds)
    return suite

def fold_in_package_vars(suite, formatter, **kwds):
    package_vars = dict()
    for group in suite['groups']:
        for package in group['packages']:
            pkgname = package['package']
            for k,v in package.items():
                package_vars['%s_%s'%(pkgname,k)] = v
            dest_install_dir = package.get('dest_install_dir') or package.get('install_dir')
            package['dest_install_dir'] = dest_install_dir
            package_vars['%s_dest_install_dir'%pkgname] = dest_install_dir

    for group in suite['groups']:
        new_packages = list()
        for package in group['packages']:
            package = update_if(package_vars, None, **package)
            new_packages.append(package)
        group['packages'] = new_packages

    if not formatter:
        formatter = PkgFormatter()
    suite = deconf.format_any(suite, formatter=formatter, **kwds)
    return suite

def load(filename, start='start', formatter = None, **kwds):

    # load in initial configuration but delay formatting
    suite = deconf.load(filename, start=start, formatter=formatter, **kwds)
    suite = fold_in_feature_requirements(suite, formatter, **kwds)
    suite = fold_in_package_vars(suite, formatter, **kwds)
    
    # from pprint import PrettyPrinter
    # pp = PrettyPrinter(indent=2)
    # pp.pprint(suite)
    return suite


# testing


def dump(filename, start='start', formatter=None):
    from pprint import PrettyPrinter
    pp = PrettyPrinter(indent=2)

    if not formatter:
        prefix ='/tmp/simple'
        formatter = PkgFormatter(prefix=prefix, PREFIX=prefix)
    data = load(filename, start=start, formatter=formatter)

    print ('Starting from "%s"' % start)
    pp.pprint(data)

if '__main__' == __name__:
    import sys
    dump(sys.argv[1:])
