#!/usr/bin/env python
'''
Package specific interpretation layered on deconf.
'''

import os
    
from . import deconf
from .util import check_output, CalledProcessError, update_if, string2list
from . import features as featmod
from . import ups
from . import rootsys

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
    ret['ups_flavor'] = ups.flavor()
    ret['root_config_arch'] = rootsys.arch()

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
        ret['ld_soname_option'] = 'install_name'
        ret['soext'] = 'dylib'
    else:
        libc_version = check_output(['ldd','--version']).split(b'\n')[0].split()[-1]
        ret['ld_soname_option'] = 'soname'
        ret['soext'] = 'so'
    ret['libc_version'] = libc_version
    ret['NCPUS'] = str(ncpus())
        
    return ret


class PkgFormatter(object):
    def __init__(self, **kwds):
        self.vars = dict()
        self.vars.update(kwds)

    def __call__(self, string, **kwds):
        if not string: return string
        vars = dict(self.vars)
        vars.update(kwds)
        try:
            ret = string.format(**vars)
        except ValueError:
            print ("%s" % string)
            raise
        return ret

def fold_in_feature_defaults(suite, formatter = None, **kwds):
    # fold in feature defaults
    for group in suite['groups']:
        new_packages = list()
        for package in group['packages']:
            featlist = string2list(package.get('features'))
            featcfg = featmod.defaults(featlist)
            package = update_if(featcfg, None, **package)            
            new_packages.append(package)
        group['packages'] = new_packages

    if not formatter:
        formatter = PkgFormatter()
    suite = deconf.format_any(suite, formatter=formatter, **kwds)
    return suite

def munge_package(package):
    '''
    Put some computed values into the package's dict
    '''
    hd = host_description()
    for k,v in hd.items():
        package.setdefault(k,v)

    tags = package.get('tags') or ''
    tags = [x.strip() for x in tags.split(',')]
    package.setdefault('tagsdashed',  '-'.join(tags))
    package.setdefault('tagsunderscore', '_'.join(tags))

    version = package.get('version')
    if version:
        version = version.format(**package)
        package.setdefault('version_2digit', '.'.join(version.split('.')[:2]))
        package.setdefault('version_underscore', version.replace('.','_'))
        package.setdefault('version_dashed', version.replace('.','-'))
        package.setdefault('version_nodots', version.replace('.',''))


    for sysdir in 'control urlfile download patch source'.split():
        package.setdefault('%s_dir' % sysdir, sysdir + 's')
    package.setdefault('install_dir', '{PREFIX}')
    package.setdefault('build_dir', 'builds/{package}-{version}')

    dest_install_dir = package.get('dest_install_dir') or package.get('install_dir')
    package['dest_install_dir'] = dest_install_dir

def fold_in_worch_values(suite, formatter, **kwds):
    for group in suite['groups']:
        for package in group['packages']:
            munge_package(package)
    if not formatter:
        formatter = PkgFormatter()
    suite = deconf.format_any(suite, formatter=formatter, **kwds)
    return suite

def fold_in_package_vars(suite, formatter, **kwds):
    package_vars = dict()

    for group in suite['groups']:
        for package in group['packages']:
#            munge_package(package)
            pkgname = package['package']

            # make uber dictionary with every package's variables
            # prefixed by the package name
            for k,v in package.items():
                p_name = '%s_%s'%(pkgname,k)
                package_vars[p_name] = v

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
    return deconf.load(filename, start=start, formatter=formatter, **kwds)

def fold_in(suite, formatter = None, **kwds):

    suite = fold_in_worch_values(suite, formatter, **kwds)
    suite = fold_in_feature_defaults(suite, formatter, **kwds)
    suite = fold_in_package_vars(suite, formatter, **kwds)
    
    return suite

def dump_suite(suite):
    from pprint import PrettyPrinter
    pp = PrettyPrinter(indent=2)
    pp.pprint(suite)



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
