#!/usr/bin/env python
'''
Configure waf for worch.

It is expected that any external tools that add worch features have already been loaded.
'''
import os
from glob import glob

import waflib.Logs as msg
from waflib import Context

from . import util
from . import pkgconf
from . import envmunge

def locate_config_files(pat):
    if os.path.exists(pat):
        return [pat]
    if pat.startswith('/'):
        return glob(pat)

    for cdir in os.environ.get('WORCH_CONFIG_PATH','').split(':') + [Context.waf_dir]:
        maybe = os.path.join(cdir,pat)
        got = glob(maybe)
        if got: return got

    return None
    

def get_orch_config_files(cfg):
    if not cfg.options.orch_config:
        raise RuntimeError('No Orchestration configuration file given (--orch-config)')
    orch_config = [] 
    okay = True
    for pat in util.string2list(cfg.options.orch_config):
        got = locate_config_files(pat)
        if got:
            orch_config += got
            continue
        msg.error('File not found: "%s"' % pat)
        okay = False
    if not okay:
        raise ValueError('no configuration files')
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

