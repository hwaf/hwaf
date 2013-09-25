#!/usr/bin/env python

from .pfi import feature
from orch.wafutil import exec_command, msg

requirements = {
    'source_dir': None,
    'source_unpacked': None,
    'unpacked_target': 'setup.py',
    'prepare_target': 'setup.py',
    'build_cmd': 'python setup.py build',
    'build_cmd_options': '',
    'build_target': None,
    'install_cmd': 'python setup.py install --prefix={python_install_dir}',
    'install_cmd_options': '',
    'install_target': None,
    'build_dir': None,
}

@feature('pypackage', **requirements)
def feature_pypackage(info):

    def prepare_task(task):
        cmd = 'cp -a %s/* %s/' % (info.source_unpacked.abspath(),
                                  info.build_dir.abspath())
        #msg.debug('orch: PYPACKAGE cmd: %r' % (cmd,))
        return exec_command(task, cmd)
    msg.debug('orch: pypackage: unpacked_target=%s' % info.unpacked_target.abspath())
    msg.debug('orch: pypackage: prepare_target=%s' % info.prepare_target.abspath())
    info.task('prepare',
              rule = prepare_task,
              source = info.unpacked_target,
              target = info.prepare_target)

    def build_task(task):
        cmd = "%s %s" % (info.build_cmd, info.build_cmd_options)
        return exec_command(task, cmd)
    info.task('build',
              source = info.prepare_target,
              target = info.build_target,
              rule = build_task)

    def install_task(task):
        cmd = "%s %s" % (info.install_cmd, info.install_cmd_options)
        return exec_command(task, cmd)
    info.task('build',
              source = info.build_target,
              target = info.install_target,
              rule = install_task)


    return
