#!/usr/bin/env pytyhon
'''
Configure waf for worch.

It is expected that any external tools that add worch features have already been loaded.
'''
import os
from glob import glob

import waflib.Logs as msg
from . import util
from . import pkgconf
from . import envmunge

def get_orch_config_files(cfg):
    if not cfg.options.orch_config:
        raise RuntimeError('No Orchestration configuration file given (--orch-config)')
    orch_config = []
    for lst in util.string2list(cfg.options.orch_config):
        lst = lst.strip()
        orch_config += glob(lst)
    okay = True
    for maybe in orch_config:
        if os.path.exists(maybe):
            continue
        msg.error('No such file: %s' % maybe)
        okay = False
    if not okay or not orch_config:
        raise ValueError('missing configuration files')
    return orch_config

def configure(cfg):
    msg.debug('orch: CONFIG CALLED')

    from . import features
    features.load()

    orch_config = get_orch_config_files(cfg)
    cfg.msg('Orch configuration files', '"%s"' % '", "'.join(orch_config))

    extra = dict(cfg.env)
    extra['top'] = cfg.path.abspath()
    out = cfg.bldnode.abspath() # usually {top}/tmp
    assert out, 'No out dir defined'
    extra['out'] = out
    extra['DESTDIR'] = getattr(cfg.options, 'destdir', '')
    msg.debug('top="{top}" out="{out}" DESTDIR="{DESTDIR}"'.format(**extra))

    suite = pkgconf.load(orch_config, start = cfg.options.orch_start, **extra)

    # load in any external tools in this configuration context that
    # may be referenced in the configuration
    for group in suite['groups']:
        for package in group['packages']:
            tools = package.get('tools')
            if not tools: continue
            for tool in util.string2list(tools):
                msg.debug('orch: loading tool: "%s" for package "%s"'  % (tool, package['package']))
                cfg.load(tool)

    suite = pkgconf.fold_in(suite, **extra)    
    #pkgconf.dump_suite(suite)


    # decompose the hierarchy of dicts into waf data
    envmunge.decompose(cfg, suite)

    cfg.msg('Orch configure envs', '"%s"' % '", "'.join(cfg.all_envs.keys()))
    msg.debug('orch: CONFIG CALLED [done]')
    return

