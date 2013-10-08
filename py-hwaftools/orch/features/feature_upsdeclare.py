#!/usr/bin/env python

import os
import shutil
from .pfi import feature
from orch.wafutil import exec_command

requirements = dict(
    ups_products = None,
    ups_product_install_dir = None,
    ups_tablegen_target = None,
    ups_qualifiers = '',
    ups_declare_target = None,
    )

@feature('upsdeclare', **requirements)
def feature_upsdeclare(info):
    '''
    ups declare $name $vstr \
	-f ANY \
	-z $products \
	-r $prod_root_dir \
	-U ups \
	-m $table_file \
	-c
    '''
    # deconstruct nodes into chunks that ups declare can digest
    # <package>/<version>/<tagsdashed>
    ups_prod_root_dir = info.ups_product_install_dir.path_from(info.ups_products)

    reltablefile = info.ups_tablegen_target.path_from(info.ups_product_install_dir)    
    # ups
    ups_sub_dir = os.path.dirname(reltablefile)
    # <package>.table
    ups_table_file = os.path.basename(reltablefile)
    
    def ups_declare_task(task):

        # always nuke previous
        version_file = info.ups_declare_target.abspath()
        if os.path.exists(version_file):
            os.remove(version_file)
        chain_file = os.path.join(os.path.dirname(version_file),'current.chain')
        if os.path.exists(chain_file):
            os.remove(chain_file)

        cmd = 'ups declare {package} v{version_underscore} -f {ups_flavor} -z {products_dir} -r {prod_root_dir} -U {ups_sub_dir} -m {table_file} -q {qualifiers} -c'
        cmd = info.format(cmd, 
                          products_dir =info.ups_products.abspath(),
                          prod_root_dir = ups_prod_root_dir,
                          ups_sub_dir = ups_sub_dir,
                          table_file = ups_table_file,
                          qualifiers = "debug",
                          )
        print ('UPS: declare cmd: "%s"' % cmd)
        return exec_command(task, cmd)
        
    info.task('upsdeclare',
              rule = ups_declare_task,
              source = info.ups_tablegen_target,
              target = info.ups_declare_target)
