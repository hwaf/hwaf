#!/usr/bin/env python
'''
Make a UPS "database".  This feature only makes sense to attached to building UPS itself.

See also the "upspkg" feature.

'''

from .pfi import feature
from orch.wafutil import exec_command

requirements = dict(
    ups_products = None,
    )

upsfiles_dbconfig_content = '''\
FILE = DBCONFIG
AUTHORIZED_NODES = *
VERSION_SUBDIR = 1
PROD_DIR_PREFIX = ${UPS_THIS_DB}
'''

@feature('upsdb', **requirements)
def feature_upsdb(info):
    '''
    Make a UPS configuration for the package
    '''
    # write content to target
    def wctt(task, content):
        out = task.outputs[0].abspath()
        #print 'UPS: writing to: %s' % out
        with open(out, "w") as fp:
            fp.write(content)
        return

    products_dir = info.ups_products
    setup_file = products_dir.make_node('setup')
    dbconfig_file = products_dir.make_node('.upsfiles/dbconfig')

    def copy_setup(task):
        src = info.build_dir.find_or_declare("ups/setup")
        cmd = "cp %s %s" % (src.abspath(), task.outputs[0].abspath())
        return exec_command(task, cmd)

    info.task("upsdatabase",
              rule = copy_setup,
              source = info.build_target,
              target = setup_file)

    info.task("upsdbconfig",
              rule = lambda task: wctt(task, upsfiles_dbconfig_content),
              source = setup_file,
              target = dbconfig_file)
    return

    
