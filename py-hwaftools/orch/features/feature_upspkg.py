#!/usr/bin/env python
'''
Make a UPS configuration for a package.  Adding this feature assures:

1) A UPS "table" file is created for the package
2) A UPS "version" file is created for the package
3) A UPS "current.chain" file is created for the package

UPS itself is not required.
'''

import os
from .pfi import feature
from orch.ups import simple_setup_table_file as gen_table_file
from orch.ups import simple_setup_version_file as gen_version_file
from orch.ups import simple_setup_chain_file as gen_chain_file

requirements = dict(
    ups_products = None,
    ups_qualifiers = None,
    )


@feature('upspkg', **requirements)
def feature_upspkg(info):
    '''
    Make a UPS configuration for the package
    '''
    # write content to target
    def wctt(task, content):
        out = task.outputs[0].abspath()
        if os.path.exists(out):
            info.debug('Not over writing UPS file: %s' % out)
            return
        #print 'UPS: writing to: %s' % out
        with open(out, "w") as fp:
            fp.write(content)
        return

    products_dir = info.ups_products

    table_file = products_dir.make_node(
        info.format('{package}/{ups_version_string}/ups/{package}.table'))
    version_file = products_dir.make_node(
        info.format('{package}/{ups_version_string}.version/{ups_flavor}_{ups_qualifiers}'))
    chain_file = products_dir.make_node(
        info.format('{package}/current.chain/{ups_flavor}_{ups_qualifiers}'))

    info.task("upstablegen",
              rule = lambda task: wctt(task, gen_table_file(**dict(info.items()))),
              update_outputs = True,
              target = table_file)

    info.task("upsversiongen",
              rule = lambda task: wctt(task, gen_version_file(**dict(info.items()))),
              update_outputs = True,
              target = version_file)

    info.task("upschaingen",
              rule = lambda task: wctt(task, gen_chain_file(**dict(info.items()))),
              update_outputs = True,
              target = chain_file)
    return
