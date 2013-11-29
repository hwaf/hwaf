#!/usr/bin/env python
'''
A waf tool to supply the modulesfile worch feature.
'''

from waflib.TaskGen import feature
import waflib.Logs as msg

import orch.features


def configure(cfg):
    orch.features.register_defaults(
        'modulesfile',
        modulesfile_dir = '{PREFIX}/modules',
        modulesfile = 'modulefile', # singular
        modulesfile_path = '{modulesfile_dir}/{package}/{version}/{modulesfile}',
    )
    return


def build(bld):

    @feature('modulesfile')
    def feature_modulesfile(tgen):

        def gen_modulefile(task):
            mfname = tgen.worch.modulesfile_path
            with open(mfname, 'w') as fp:
                fp.write('#%Module1.0 #-*-tcl-*-#\n')

                for mystep, deppkg, deppkgstep in tgen.worch.dependencies():
                    load = 'module load %s/{%s_version}' % (deppkg, deppkg)
                    load = tgen.worch.format(load)
                    fp.write(load + '\n')

                for var, val, oper in tgen.worch.exports():
                    if oper == 'set':
                        fp.write('setenv %s %s\n' % (var, val))
                    if oper == 'prepend':
                        fp.write('prepend-path %s %s\n' % (var, val))
                    if oper == 'append':
                        fp.write('append-path %s %s\n' % (var, val))

            return 0

        tgen.step('modulesfile',
                  rule = gen_modulefile,
                  source = tgen.control_node('install'),
                  target = tgen.make_node(tgen.worch.modulesfile_path))
        
    return
