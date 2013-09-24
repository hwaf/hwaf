#!/usr/bin/env python
from .pfi import feature
from orch.wafutil import exec_command

requirements = {
    'unpacked_target': None,
    'source_unpacked': None,
    'prepare_cmd': None,
    'prepare_cmd_options': None,
    'prepare_target': None,
    'build_dir': None,
}

def generic(info):
    def prepare_task(task):
        cmd = "%s %s" % (info.prepare_cmd, info.prepare_cmd_options)
        return exec_command(task, cmd)
        
    info.task('prepare',
              rule = prepare_task,
              source = info.unpacked_target,
              target = info.prepare_target)

@feature('prepare', **requirements)
def feature_prepare(info):
    return generic(info)


