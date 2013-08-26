#!/usr/bin/env python
'''
Package specific interpretation layered on deconf.
'''

import os

import subprocess
from subprocess import CalledProcessError

try:
    from subprocess import check_output
except ImportError:
    class CalledProcessError(Exception):
        """This exception is raised when a process run by check_call() or
        check_output() returns a non-zero exit status.
        The exit status will be stored in the returncode attribute;
        check_output() will also store the output in the output attribute.
        """
        def __init__(self, returncode, cmd, output=None):
            self.returncode = returncode
            self.cmd = cmd
            self.output = output
        def __str__(self):
            return "Command '%s' returned non-zero exit status %d" % (self.cmd, self.returncode)

    def check_output(*popenargs, **kwargs):
        r"""Run command with arguments and return its output as a byte string.

        If the exit code was non-zero it raises a CalledProcessError.  The
        CalledProcessError object will have the return code in the returncode
        attribute and output in the output attribute.

        The arguments are the same as for the Popen constructor.  Example:

        >>> check_output(["ls", "-l", "/dev/null"])
        'crw-rw-rw- 1 root root 1, 3 Oct 18  2007 /dev/null\n'

        The stdout argument is not allowed as it is used internally.
        To capture standard error in the result, use stderr=STDOUT.

        >>> check_output(["/bin/sh", "-c",
        ...               "ls -l non_existent_file ; exit 0"],
        ...              stderr=STDOUT)
        'ls: non_existent_file: No such file or directory\n'
        """
        if 'stdout' in kwargs:
            raise ValueError('stdout argument not allowed, it will be overridden.')
        process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
        output, unused_err = process.communicate()
        retcode = process.poll()
        if retcode:
            cmd = kwargs.get("args")
            if cmd is None:
                cmd = popenargs[0]
            raise CalledProcessError(retcode, cmd, output=output)
        return output
    
from . import deconf

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

    ret['gcc_dumpversion'] = check_output(['gcc','-dumpversion']).strip()
    ret['gcc_dumpmachine'] = check_output(['gcc','-dumpmachine']).strip()
    try:
        ma = check_output(['gcc','-print-multiarch']).strip() # debian-specific
    except CalledProcessError:
        ma = ""
    ret['gcc_multiarch'] = ma
    if 'darwin' in ret['kernelname'].lower():
        libc_version = ret['kernelversion'] # FIXME: something better on Mac ?
    else:
        libc_version = check_output(['ldd','--version']).split(b'\n')[0].split()[-1]
    ret['libc_version'] = libc_version

    return ret


class PkgFormatter(object):
    def __init__(self, **kwds):
        self.vars = host_description()
        self.vars.update(kwds)

    def __call__(self, string, **kwds):
        if not string: return string
        tags = kwds.get('tags')
        if tags:
            tags = [x.strip() for x in tags.split(',')]
            kwds.setdefault('tagsdashed',  '-'.join(tags))
            kwds.setdefault('tagsunderscore', '_'.join(tags))

        version = kwds.get('version')
        if version:
            kwds.setdefault('version_2digit', '.'.join(version.split('.')[:2]))
            kwds.setdefault('version_underscore', version.replace('.','_'))
            kwds.setdefault('version_nodots', version.replace('.',''))
        vars = dict(self.vars)
        vars.update(kwds)
        ret = string.format(**vars)

        # print 'formatting "%s" with:' %string
        # from pprint import PrettyPrinter
        # pp = PrettyPrinter(indent=2)
        # pp.pprint(vars)
        # print 'got: "%s"' % ret
        return ret


def load(filename, start='start', formatter = None, **kwds):
    if not formatter:
        formatter = PkgFormatter()
    suite = deconf.load(filename, start=start, formatter=formatter, **kwds)
    
    # post-process
    install_dirs = {}
    for group in suite['groups']:
        for package in group['packages']:
            pkgname = package['package']
            install_dir = package['install_dir']
            install_dirs['%s_install_dir'%pkgname] = install_dir

    for group in suite['groups']:
        to_replace = []
        for package in group['packages']:
            new = deconf.format_flat_dict(package,**install_dirs)
            to_replace.append(new)
        group['packages'] = to_replace
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
