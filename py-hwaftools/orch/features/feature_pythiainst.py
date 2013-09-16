#!/usr/bin/env python
'''
Install pythia6 assuming tarball feature has been used
'''

from .pfi import feature
from orch.wafutil import exec_command

requirements = {
    'unpacked_target': 'pythia6416.f',
    'source_unpacked': 'pythia6',
    'prepare_cmd': None,
    'prepare_cmd_options': None,
    'prepare_target': None,
    'build_dir': None,
    'build_target': 'libPythia6.so',
    'install_target' : 'lib/libPythia6.so',
}
@feature('pythiainst', **requirements)
def feature_pythiainst(info):

    f1 = info.node('pythia6416.f', info.build_dir)
    f2 = info.node('tpythia6_called_from_cc.F', info.build_dir)
    c1 = info.node('main.c', info.build_dir)
    c2 = info.node('pythia6_common_address.c', info.build_dir)

    fo1 = info.node('pythia6416.o', info.build_dir)
    fo2 = info.node('tpythia6_called_from_cc.o', info.build_dir)
    co1 = info.node('main.o', info.build_dir)
    co2 = info.node('pythia6_common_address.o', info.build_dir)

    info.task('prepare',
              rule = "cp %s/* ." % info.source_unpacked.abspath(),
              source = info.unpacked_target,
              target = [f1, f2, c2],
              cwd = info.build_dir.abspath())

    info.task('genmain',
              rule = "echo 'void MAIN__() {}' > main.c",
              source = f1,
              target = c1,
              cwd = info.build_dir.abspath())

    info.task('buildc1',
              rule = 'gcc -c -fPIC %s' % c1,
              source = c1,
              target = co1,
              cwd = info.build_dir.abspath())

    info.task('buildc2',
              rule = 'gcc -c -fPIC %s' % c2,
              source = c2,
              target = co2,
              cwd = info.build_dir.abspath())

    info.task('buildf1',
              rule = 'gfortran -c -fPIC %s' % f1,
              source = f1,
              target = fo1,
              cwd = info.build_dir.abspath())

    info.task('buildf2',
              rule = 'gfortran -c -fPIC -fno-second-underscore %s'%f2,
              source = f2,
              target = fo2,
              cwd = info.build_dir.abspath())

    info.task('build',
              rule = 'gfortran -shared -Wl,-soname,libPythia6.so -o %s main.o  pythia*.o tpythia*.o' % info.build_target,
              source = [co1, co2, fo1, fo2],
              target = info.build_target,
              cwd = info.build_dir.abspath())
            
    info.task('install',
              rule = 'cp %s %s' % (info.build_target.abspath(), info.install_target.abspath()),
              source = info.build_target,
              target = info.install_target)

              
