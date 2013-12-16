#!/usr/bin/env python
'''
Utility functions
'''
import re

try:    from urllib import request
except: from urllib import urlopen
else:   urlopen = request.urlopen


def string2list(string, delims=', '):
    if not isinstance(string, type('')):
        return string
    return re.split('[%s]+'%delims, string)

def update_if(d, p, **kwds):
    '''Return a copy of d updated with kwds.

    If no such item is in d, set item from kwds, else call p(k,v) with
    kwds item and only set if returns True.

    '''
    if p is None:
        p = lambda k,v: v is not None 
    d = dict(d)                 # copy
    for k,v in kwds.items():
        if not k in d:
            d[k] = v
            continue
        if p(k, v):
            d[k] = v

    return d

    
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


def envvars(envtext):
    '''
    Parse envtext as lines of 'name=value' pairs, return result as a
    dictionary.  Values beginning with '()' are allowed to span
    multiple lines and expected to end with a closing brace.
    '''
    def lines(text):
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            yield line
    lines = lines(envtext)      # this looses the first?

    ret = dict()
    for line in lines:
        name, val = line.split('=',1)
        if not val.startswith('()') or val.endswith('}'):
            ret[name] = val
            continue

        # we have a multi-lined shell function, slurp until we get an ending '}'
        val = [val]
        for line in next(lines):
            val.append(line)
            if line.endswith('}'):
                break
            continue
        ret[name] = '\n'.join(val)
    return ret

def get_unpacker(filename, dirname = '.'):
    if filename.endswith('.zip'): 
        return 'unzip -d %s %s' % (dirname, filename)
    
    text2flags = {'.tar.gz':'xzf', '.tgz':'xzf', '.tar.bz2':'xjf', '.tar':'xf' }
    for ext, flags in text2flags.items():
        if filename.endswith(ext):
            return 'tar -C %s -%s %s' % (dirname, flags, filename)
    return 'tar -C %s -xf %s' % (dirname, filename)

