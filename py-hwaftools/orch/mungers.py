#!/usr/bin/env python
'''
This module primarily provides the functions:

 - construct :: create mungers from configuration items
 - apply :: apply a list of mungers to an environment

In this module "environment munging" or "munge" refers to mutating a
dictionary of environment variables.  

A munger is a callable object with the signature:

  munger(**environ) --> new_environ

The returned environment is a copy an so mungers may be chained via apply().

Mungers are constructed from key/value configuration items like:

  <prefix><name> = <command><delim><payload>

Where:

 - prefix :: indicates some domain ("export_", "buildenv_").  Note it includes any separator character(s)
 - name :: a <command>-specific label.  For commands setting specific environment variables it provides the variable name.  For shell commands it is ignored (but may be used for ordering).
 - command :: one of "append", "prepend", "set" or "shell".  If not of this set then "set" is assumed and no <delim> is expected
 - delim :: A single character delimiter used for "append" and "prepend" commands and otherwise required but ignored (unless no command given as above)
 - payload :: the value to apply to the command.  For "shell" commands it is a shell command line, for all else it is an environment variable value.

'''

import os
import tempfile

from . import util

def split_var_munger_command(cmdstr, cmd):
    'cmd<delim><string> --> (<delim>,<string>'
    rest = cmdstr[len(cmd):]
    return rest[0], rest[1:]

def update_var(name, cmdstr, **environ):
    '''
    A munger body which will apply the cmdstr to the named environment
    variable to the given environ keywords and return the result.
    '''
    #print 'munger: apply: %s: "%s"' % (name, cmdstr)

    oldval = environ.get(name)
    if cmdstr.startswith('append'):
        delim,val = split_var_munger_command(cmdstr, 'append')
        newval = oldval + delim + val if oldval else val
    elif cmdstr.startswith('prepend'):
        delim,val = split_var_munger_command(cmdstr, 'prepend')
        newval = val + delim + oldval if oldval else val
    elif cmdstr.startswith('set'):
        delim,val = split_var_munger_command(cmdstr, 'set')
        newval = val
    else: 
        newval = cmdstr
    environ[name] = newval
    return environ
            

# by default, rely on this being in the PATH
env_executable = "env"
def cmd_munger(cmd, **environ):
    '''
    A munger body which will execute the shell cmd in the given
    environment and return the post-execution environment.  This is
    done by parsing the output to the "env" command as set by the
    "env_executable" variable.
    '''
    #print 'munger: apply: "%s"' % cmd
    #print 'PATH=%s' % environ.get('PATH','')
    fd, fname = tempfile.mkstemp()
    cmd += ' && %s > %s' % (env_executable, fname)
    util.check_output(cmd, shell=True, env=environ)
    os.close(fd)
    envtext = open(fname).read()
    ret = dict()
    for k,v in util.envvars(envtext).items():
        ret[k.strip()] = v.strip()
    return ret

def make_munger(name, cmdstr):
    '''
    Dispatch based on the command of the cmdstr (<command><delim><payload>).

    Returns a munger object.
    '''
    #print 'munger: %s: "%s"' % (name, cmdstr) 
        
    if cmdstr.startswith('shell'):
        delim, cmdline = split_var_munger_command(cmdstr, 'shell')
        return lambda **environ: cmd_munger(cmdline, **environ)
    return lambda **environ: update_var(name, cmdstr, **environ)

def construct(prefix, **pkg_kwds):
    '''
    Any package configuration items with keys starting with prefix are
    interpreted as munging commands.
    '''

    ret = list()
    for key, cmdstr in pkg_kwds.items():
        if not key.startswith(prefix):
            continue
        name = key[len(prefix):]
        m = make_munger(name, cmdstr)
        ret.append(m)
    return ret

def apply(mungers, **environ):
    '''
    Run the given environment through the given mungers and return the result.

    If no keyword arguments are given the current process environment
    (os.environ) is used as a starting environment..
    '''
    if not environ:
        environ = dict(os.environ)
    for m in mungers:
        environ = m(**environ)
    return environ
