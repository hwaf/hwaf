#!/usr/bin/env python

import os.path as osp
from glob import glob
from orch.util import update_if
from . import requirements as reqmod
import waflib.Logs as msg

def load():
    
    mydir = osp.dirname(__file__)
    for fpath in glob("%s/feature_*.py"%mydir):
        ffile = osp.basename(fpath)
        modname = osp.splitext(ffile)[0]
        exec("from . import %s"%modname)
    from . import pfi
    return (pfi.registered_func, pfi.registered_config)

def feature_requirements(featlist):
    funcs, cfgs = load()
    all_featcfg = reqmod.valuedict()
    for feat in featlist:
        featcfg = cfgs.get(feat)
        if not featcfg:
            msg.debug('No feature config for feature "%s' % feat)
            continue
        all_featcfg = update_if(all_featcfg, None, **featcfg)
    return all_featcfg

