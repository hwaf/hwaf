#!/usr/bin/env python
# encoding: utf-8

## stdlib imports
import os
from glob import glob

## 3rd party
from . import pkgconf
from . import envmunge
from . import features as featmod
from . import util

## waf imports
import waflib.Logs as msg

# NOT from the waf book.  The waf book example for depends_on doesn't work
from waflib import TaskGen
@TaskGen.feature('*') 
@TaskGen.before_method('process_rule')
def post_the_other(self):
    deps = getattr(self, 'depends_on', []) 
    for name in self.to_list(deps):
        msg.debug('orch: DEPENDS_ON: %s %s' % ( self.name, name ))
        other = self.bld.get_tgen_by_name(name) 
        other.post()
        for ot in other.tasks:
            msg.debug('orch: OTHER TASK: %s before: %s' % (ot, ot.before))
            ot.before.append(self.name)


# waf entries
def options(opt):
    opt.add_option('--orch-config', action = 'store', default = 'orch.cfg',
                   help='Give an orchestration configuration file.')
    opt.add_option('--orch-start', action = 'store', default = 'start',
                   help='Set the section to start the orchestration')

def bind_functions(ctx):
    from pprint import PrettyPrinter
    pp = PrettyPrinter(indent=2)
    ctx.orch_dump = lambda : pp.pprint({'packages': ctx.env.orch_package_list,
                                        'groups': ctx.env.orch_group_list})


def configure(cfg):
    msg.debug('orch: CONFIG CALLED')

    if not cfg.options.orch_config:
        raise RuntimeError('No Orchestration configuration file given (--orch-config)')
    orch_config = []
    for lst in cfg.options.orch_config.split(','):
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
            
    cfg.msg('Orch configuration files', '"%s"' % '", "'.join(orch_config))

    extra = dict(cfg.env)
    extra['top'] = cfg.path.abspath()
    extra['DESTDIR'] = getattr(cfg.options, 'destdir', '')
    suite = pkgconf.load(orch_config, start = cfg.options.orch_start, **extra)

    envmunge.decompose(cfg, suite)

    cfg.msg('Orch configure envs', '"%s"' % '", "'.join(cfg.all_envs.keys()))
    bind_functions(cfg)
    return

def build(bld):
    msg.debug ('orch: BUILD CALLED')

    bind_functions(bld)

    import orch.features
    feature_funcs, feature_configs = orch.features.load()
    msg.info('Supported features: "%s"' % '", "'.join(feature_funcs.keys()))

    msg.debug('orch: Build envs: %s' % ', '.join(bld.all_envs.keys()))

    pfi_list = list()
    to_recurse = []

    for grpname in bld.env.orch_group_list:
        msg.debug('orch: Adding group: "%s"' % grpname)
        bld.add_group(grpname)
        group = bld.env.orch_group_dict[grpname]
        for package in group['packages']:
            pkgname = package['package']

            # delegate package to another wscript file?
            other_wscript = os.path.join(bld.launch_dir, pkgname, 'wscript')
            if os.path.exists(other_wscript):
                msg.info('orch: delegating to %s' % other_wscript)
                to_recurse.append(pkgname)
                continue

            pkgcfg = bld.env.orch_package_dict[pkgname]
            featlist = pkgcfg.get('features').split()
            msg.debug('orch: features for %s: "%s"' % (pkgname, '", "'.join(featlist)))
            for feat in featlist:
                try:
                    feat_func = feature_funcs[feat]
                except KeyError:
                    msg.error('No method for feature: "%s", package: "%s"'%(feat,pkgname))
                    raise
                msg.debug('orch: feature: "%s" for package: "%s"' % (feat, pkgname))
                pfi = feat_func(bld, pkgcfg)
                pfi_list.append(pfi)

    if to_recurse:
        bld.recurse(to_recurse)

    for pfi in pfi_list:
        pfi.register_dependencies()

    msg.debug ('orch: BUILD CALLED [done]')
