#!/usr/bin/env python

import os.path as osp
from glob import glob

import waflib.Logs as msg

registered_defaults = dict()  # feature name -> configuration dictionary

def load():
    msg.debug('orch: loading features')

    mydir = osp.dirname(__file__)
    for fpath in glob("%s/feature_*.py"%mydir):
        ffile = osp.basename(fpath)
        modname = osp.splitext(ffile)[0]
        msg.debug('orch: loading module: "%s"' % modname)
        exec("from . import %s"%modname)

def defaults(feats):
    ret = dict()
    for toe in feats:
        d = registered_defaults.get(toe)
        if d:
            ret.update(d)
    return ret

def register_defaults(name, **kwds):
    '''Register a set of default feature configuration items which may be
    overridden by user configuration.
    '''
    registered_defaults[name] = kwds

