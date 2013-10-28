#!/usr/bin/env python
'''
Make a modules.sf.net modulefile for the package.
'''

from .pfi import feature
from orch.wafutil import exec_command

requirements = {
    'install_dir': None,
    'install_target': None,
    'modulefile_target': None,
    'modules_dir' : None,
}


@feature('modulefile', **requirements)
def feature_modulefile(info):

    def gen_modulefile(task):
        mfname = info.modulefile_target.abspath()
        with open(mfname, 'w') as fp:
            fp.write('#%Module1.0 #-*-tcl-*-#\n')

            for mystep, deppkg, deppkgstep in info.dependencies():
                load = 'module load %s {%s_version}' % (deppkg, deppkg)
                load = info.format(load)
                fp.write(load + '\n')

            for var, val, oper in info.exports():
                if oper == 'set':
                    fp.write('setenv %s %s\n' % (var, val))
                if oper == 'prepend':
                    fp.write('prepend-path %s %s\n' % (var, val))
                if oper == 'append':
                    fp.write('append-path %s %s\n' % (var, val))

        return 0

    info.task('modulefile',
              rule = gen_modulefile,
              source = info.install_target,
              target = info.modulefile_target)
