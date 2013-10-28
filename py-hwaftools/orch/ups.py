#!/usr/bin/env python
'''
A ten foot pole
'''

import os
import time
from .util import check_output, CalledProcessError

def flavor():
    '''
    Ow, my balls.
    '''
    try:
        flav = check_output(['ups','flavor'])
        #print 'UPS FLAVOR from ups: "%s"' % flav
        return flav.strip()
    except OSError:
        #print 'UPS failed to run, calculate flavor manually'
        pass

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


def worch_export_to_ups_command(wk, wv):
    var = wk[len('export_'):]

    if wv.startswith('prepend:'):
        val = wv[len('prepend:'):]
        return 'pathPrepend(%s, %s)' % (var, val)

    if wv.startswith('append:'):        
        val = wv[len('append:'):]
        return 'pathAppend(%s, %s)' % (var, val)

    if wv.startswith('set:'):
        val = wv[len('set:'):]
        return 'envSet(%s, %s)' % (var, val)

    val = wv
    return 'envSet(%s, %s)' % (var, val)
    

def simple_setup_table_file(**cfg):
    '''
    Return the contents of a UPS table file to set up the package via
    UPS.

    The table file is "simple" in the sense that it applies only for
    the given package configuration items.
    '''

    commands = []
    for k,v in cfg.items():
        if k.startswith('export_'):
            commands.append(worch_export_to_ups_command(k,v))

    stf = '''\
File = Table
Product = {package}

Group:
  Flavor = {ups_flavor}
  Qualifiers = "{ups_qualifiers}"
Common:
  Action = SETUP
    setupEnv()
    prodDir()
    {commands}
End:
'''.format(commands = '    \n'.join(commands), **cfg)
    return stf

def simple_setup_version_file(**cfg):
    '''
    Return the contents of a UPS version file

    FIXME: it makes some assumptions as to UPS directory structure.
    '''
    content = '''\
FILE = version
PRODUCT = {package}
VERSION = {ups_version_string}

#*************************************************
#
FLAVOR = {ups_flavor}
QUALIFIERS = "{ups_qualifiers}"
  DECLARER = {user}
  DECLARED = {date}
  MODIFIER = {user}
  MODIFIER = {date}
  PROD_DIR = {ups_prod_subdir}
  UPS_DIR = ups
  TABLE_FILE = {package}.table
'''.format(user = os.environ.get('USER','unknown'),
           date = time.strftime('%Y-%m-%d %H.%M.%S GMT', time.gmtime(time.time())),
           **cfg)
    return content

def simple_setup_chain_file(**cfg):
    '''
    Return the contents of a UPS chain file

    FIXME: it only make "current chain".
    '''
    content = '''\
FILE = chain
PRODUCT = {package}
CHAIN = current

#*************************************************
#
FLAVOR = {ups_flavor}
VERSION = {ups_version_string}
QUALIFIERS = "{ups_qualifiers}"
  DECLARER = {user}
  DECLARED = {date}
  MODIFIER = {user}
  MODIFIER = {date}
'''.format(user = os.environ.get('USER','unknown'),
           date = time.strftime('%Y-%m-%d %H.%M.%S GMT', time.gmtime(time.time())),
           **cfg)
    return content
