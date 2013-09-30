#!/usr/bin/env python
# encoding: ISO8859-1

import os
import sys
from pkgutil import get_data
from glob import glob
import zipfile

cwd = os.getcwd()

def dump_out(what):
    if os.path.exists(what):
        print ('%s already produced' % what)
        return
    print 'Dumping %s' % what
    with open(what, 'w') as fp:
        data = get_data('bundle', what)
        fp.write(data)

def prepare_waf():
    
    if not os.path.exists('waf'):
        dump_out('waf')

    os.system('chmod +x waf')

    ret = os.system('./waf --version')
    if ret != 0:
        print ('Failed to run waf')
        sys.exit (ret)
        
    wafdir = glob('.waf-*')
    if not wafdir:
        print ('No .waf-* directory produced')
        sys.exit(1)
    return wafdir[0]

def unzip_to(filename, todir = '.'):
    if not os.path.exists(filename):
        dump_out(filename)
    zf = zipfile.ZipFile(filename, 'r')
    zf.extractall(todir)

def remove(*args):
    for dead in args:
        if os.path.exists(dead):
            print 'Removing %s' % dead
            os.remove(dead)

def wafdir2wafver(wafdir):
    return wafdir.split('-')[1]

def assure_unpack():
    wafdir = glob('.waf-*')
    if wafdir and os.path.exists(wafdir[0]):
        return wafdir[0]

    wafdir = prepare_waf()
    dump_out('wscript')
    unzip_to('orch.zip',wafdir)
    unzip_to('cfg.zip')
    remove('cfg.zip', 'orch.zip', 'waf')
    return wafdir

def main():
    wafdir = assure_unpack()
    wafver = wafdir2wafver(wafdir)

    sys.path.insert(0, os.path.realpath(wafdir))
    from waflib import Scripting
    Scripting.waf_entry_point(cwd, wafver, wafdir)
    
