#!/usr/bin/env python
'''
The worch build tool for waf.  

This calls the build context on every package in configured list of orch groups.  

All worch feature methods are expected to be imported already.

FIXME: recursion to external wscript files has been removed.
'''

import waflib.Logs as msg
from waflib.TaskGen import feats as available_features
from . import util, wafutil


def assert_features(pkgcfg):
    features = util.string2list(pkgcfg['features'])
    for feat in features:
        assert feat in available_features.keys(), 'Unknown feature "%s" for package "%s"' % (feat, pkgcfg['package'])
        

def build(bld):
    msg.debug ('orch: BUILD CALLED')

    # batteries-included
    from . import features
    features.load()

    # external tools
    for pkgname, pkgdict in bld.env.orch_package_dict.items():
        tools = pkgdict.get('tools')
        if not tools: continue
        for tool in util.string2list(tools):
            bld.load(tool)

    from waflib.TaskGen import feats as available_features
    msg.debug('orch: available features: %s' % (', '.join(sorted(available_features.keys())), ))

    msg.info('Supported waf features: "%s"' % '", "'.join(sorted(available_features.keys())))
    msg.debug('orch: Build envs: %s' % ', '.join(sorted(bld.all_envs.keys())))

    for grpname in bld.env.orch_group_list:

        msg.debug('orch: Adding group: "%s"' % grpname)
        bld.add_group(grpname)

        group = bld.env.orch_group_dict[grpname]
        for package in group['packages']:
            pkgname = package['package']

            assert_features(package)

            pkgcfg = bld.env.orch_package_dict[pkgname]
            bld.worch_package(pkgcfg)


    bld.add_pre_fun(pre_process)
    bld.add_post_fun(post_process)
    msg.debug ('orch: BUILD CALLED [done]')

def pre_process(bld):
    msg.debug('orch: PREPROCESS')
def post_process(bld):
    msg.debug('orch: POSTPROCESS')
