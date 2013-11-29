#!/usr/bin/env python
'''
Feature to run a command

It requires no previous steps.  It provides the 'command' step.  The
command_cmd is used as a source for the step.  It should be specified
with an absolute path or if relative, w.r.t. the command_dir.
'''

from waflib.TaskGen import feature
import waflib.Logs as msg

from orch.util import urlopen

import orch.features
orch.features.register_defaults(
    'command',
    command_dir = '.',
    command_cmd_prefix = '',
    command_cmd_postfix = '',
    command_cmd = None,
    command_cmd_options = '',
    command_target = None,
)

@feature('command')
def feature_command(tgen):
    '''
    Run a command
    '''
    cmd_dir = tgen.make_node(tgen.worch.command_dir)
    cmd_node = cmd_dir.make_node(tgen.worch.command_cmd)
    cmd_target = tgen.worch.command_target
    if cmd_target:
        map(tgen.make_node, tgen.to_list(cmd_target))
    cmd_rule = '{command_cmd_prefix}{command_cmd} {command_cmd_options} {command_cmd_postfix}'
    tgen.step('command',
              rule = tgen.worch.format(cmd_rule),
              source = cmd_node,
              target = cmd_target or "",
              cwd = cmd_dir.abspath())

    return
