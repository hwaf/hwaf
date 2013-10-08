#!/usr/bin/env python

import os
from .pfi import feature
from orch.ups import simple_setup_table_file as table_file
import waflib.Logs as msg

requirements = dict(
    install_target = None,
    ups_products = None,
    ups_product_install_dir = None,
    ups_tablegen_target = None,
    ups_qualifiers = '',
    )

@feature('upstablegen', **requirements)
def feature_upstablegen(info):

    def ups_table_gen_task(task):
        filename = info.ups_tablegen_target.abspath()
        if os.path.exists(filename):
            blah = 'UPS table file already exists: %s' % filename
            print ("%s" % blah)
            msg.debug(blah)
            return 0
        upsdir = os.path.dirname(filename)
        if not os.path.exists(upsdir):
            os.makedirs(upsdir)

        print ('UPS writing table file: %s' % filename)
        tf = table_file(**dict(info.items()))
        print ("%s" % tf)
        with open(filename, 'w') as fp:
            fp.write(tf + '\n')
        return 0

    info.task('upstablegen',
              rule = ups_table_gen_task,
              source = info.install_target,
              target = info.ups_tablegen_target,
              cwd = info.build_dir)
