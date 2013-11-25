#!/usr/bin/env python
'''
Features for prepare source code.  

 - prepare :: generic
 - autoconf :: run "configure" script found in source directory
 - cmake :: run cmake

These features all rely on the "unpack" step to have run.  It produces a "prepare" step.
'''


from waflib.TaskGen import feature
import waflib.Logs as msg

from orch.wafutil import exec_command
import orch.features

orch.features.register_defaults(
    'prepare',
    source_unpacked_path = '{source_dir}/{source_unpacked}',
    prepare_cmd = None,         # must provide
    prepare_cmd_std_opts = '',
    prepare_cmd_options = '',
    prepare_target = None,      # must provide
    prepare_target_path = '{build_dir}/{prepare_target}',
)

@feature('prepare')
def feature_prepare(tgen):

    cmdstr = tgen.worch.format('{prepare_cmd} {prepare_cmd_std_opts} {prepare_cmd_options}')
    tgen.step('prepare',
              rule = cmdstr,
              source = tgen.control_node('unpack'),
              target = tgen.worch.prepare_target_path)



orch.features.register_defaults(
    'autoconf',
    source_unpacked_path = '{source_dir}/{source_unpacked}',
    prepare_cmd = '{source_unpacked_path}/configure',
    prepare_cmd_std_opts = '--prefix={install_dir}',
    prepare_cmd_options = '',
    prepare_target = 'config.status',
    prepare_target_path = '{build_dir}/{prepare_target}',
)

@feature('autoconf')
def feature_autoconf(tgen):

    cmdstr = tgen.make_node(tgen.worch.prepare_cmd).abspath()
    cmdstr += tgen.worch.format(' {prepare_cmd_std_opts} {prepare_cmd_options}')
    tgen.step('prepare',
              rule = cmdstr,
              #after = tgen.worch.package + '_unpack',
              source = tgen.control_node('unpack'),
              target = tgen.worch.prepare_target_path)
        
orch.features.register_defaults(
    'cmake',
    source_unpacked_path = '{source_dir}/{source_unpacked}',
    prepare_cmd = 'cmake',
    prepare_cmd_std_opts = '-DCMAKE_INSTALL_PREFIX={install_dir}',
    prepare_cmd_options = '',
    prepare_target = 'CMakeCache.txt',
    prepare_target_path = '{build_dir}/{prepare_target}',
)

@feature('cmake')
def feature_cmake(tgen):
    cmkfile = tgen.make_node(tgen.worch.source_unpacked_path + '/CMakeLists.txt')

    def prepare(task):
        cmdstr = '{prepare_cmd} {srcdir} {prepare_cmd_std_opts} {prepare_cmd_options}'
        cmd = tgen.worch.format(cmdstr, srcdir=cmkfile.parent.abspath())
        return exec_command(task, cmd)

    #msg.debug('orch: cmkfile: %s' % cmkfile.abspath())
    tgen.step('prepare',
              rule = prepare,
              source = [tgen.control_node('unpack')],
              target = tgen.worch.prepare_target_path)
