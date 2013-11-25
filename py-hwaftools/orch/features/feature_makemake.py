#!/usr/bin/env python
'''
Features to do a "make" double-pump.

This feature rely on the "prepare" step to have run.  It produces "build" and "install" steps.

'''

from waflib.TaskGen import feature
import waflib.Logs as msg

from orch.wafutil import exec_command
import orch.features

orch.features.register_defaults(
    'makemake',
    build_cmd = 'make',
    build_cmd_options = '',
    build_target = '',
    build_target_path = '{build_dir}/{build_target}',
    
    install_cmd = 'make install',
    install_cmd_options = '',   # please don't set DESTDIR implicitly
    install_target = '',
    install_target_path = '{install_dir}/{install_target}',
)

@feature('makemake')
def feature_makemake(tgen):

    def build(task):
        cmdstr = '{build_cmd} {build_cmd_options}'
        cmd = tgen.worch.format(cmdstr)
        return exec_command(task, cmd)
    tgen.step('build',
              rule = build,
              source = tgen.control_node('prepare'),
              target = tgen.worch.build_target_path)

    def install(task):
        cmdstr = '{install_cmd} {install_cmd_options}'
        cmd = tgen.worch.format(cmdstr)
        return exec_command(task, cmd)
    tgen.step('install',
              rule = install,
              source = tgen.control_node('build'),
              target = tgen.make_node(tgen.worch.install_target_path))
