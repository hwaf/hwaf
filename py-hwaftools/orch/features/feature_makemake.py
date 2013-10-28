#!/usr/bin/env python
'''
A feature that does a double-pump make.  Once to build and once to install
'''
from .pfi import feature
from orch.wafutil import exec_command

requirements = {
    'prepare_target': None,

    'build_dir' : None,
    'build_cmd' : 'make',
    'build_cmd_options' : '',
    'build_target': None,

    'install_cmd' : 'make install',
    'install_cmd_options' : 'DESTDIR={DESTDIR}',
    'install_target': None,

}

def build(info):

    def build_task(task):
        cmd = "%s %s" % ( info.build_cmd, info.build_cmd_options )
        return exec_command(task, cmd)
        
    info.task('build',
              rule = build_task,
              source = info.prepare_target,
              target = info.build_target,
              cwd = info.build_dir.abspath())
    return

def install(info):


    def install_task(task):
        cmd = "%s %s" % ( info.install_cmd, info.install_cmd_options )
        return exec_command(task, cmd)
        
    info.task('install',
              rule = install_task,
              source = info.build_target,
              target = info.install_target)

    return

@feature('makemake', **requirements)
def feature_makemake(info):
    build(info)
    install(info)
    return


