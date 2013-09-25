#!/usr/bin/env python
'''
The VCS feature downloads and unpacks a source archive stored in a
version control system.  It is a drop-in replacement for the "tarball"
feature.  Its final step is "unpack".

Some VCS flavors may place the cloned repository under download_dir
followed by producing the unpacked source.  Others may directly
checkout to the unpacked source directory.
'''

import os.path as osp
from .pfi import feature
from orch.wafutil import exec_command

#from orch.util import urlopen

requirements = {
    'source_urlfile': None,
    'source_url': None,
    'source_dir': None,
    'source_unpacked': None,
    'unpacked_target': None,

    'vcs_flavor': None,
    'vcs_tag' : '',
    'vcs_module': None,
}

    # def checkout_task(task):
    #     meth = eval('do_%s' % flavor)
    #     cmd = meth(info)
    #     return exec_command(task, cmd)
    # info.task('unpack',
    #           rule = checkout_task,
    #           source = info.source_urlfile,
    #           target = info.unpacked_target,

def single_cmd_rule(func):
    def rule(info):
        def task_func(task):
            cmd = func(info)
            return exec_command(task, cmd)
        info.task('unpack',
                  rule = task_func,
                  source = info.source_urlfile,
                  target = info.unpacked_target)
    return rule

@single_cmd_rule
def do_cvs(info):
    tag = getattr(info, 'vcs_tag', '')
    if tag:
        tag = '-r ' + tag
    module = getattr(info, 'vcs_module', '')
    if not module:
        module = info.package
    pat = 'cvs -d {source_url} checkout {vcs_tag_opt} -d {source_unpacked} {module}'
    return info.format(pat, vcs_tag_opt=tag, module=module)

@single_cmd_rule
def do_svn(info):
    if getattr(info, 'vcs_tag'):
        err = info.format('SVN has no concept of tags, can not honor: "{vcs_tag}"')
        info.error(err)
        raise ValueError(err)
    pat = "svn checkout {source_url} {source_unpacked}"
    return info.format(pat)


@single_cmd_rule
def do_hg(info):
    tag = getattr(info, 'vcs_tag', '')
    if tag:
        tag = '-b ' + tag
    pat = "hg clone {vcs_tag_opt} {source_url} {source_unpacked}"
    return info.format(pat, vcs_tag_opt=tag)


def do_git(info):

    # note: it's a slight cheat to not have this in a requirement but
    # the other do_* functions do not make in intermediate repository
    git_dir = info.node(info.format('{package}.git'), info.download_dir)

    def clone_or_update(task):
        if osp.exists(git_dir.abspath()):
            cmd = 'git --git-dir={git_dir} fetch --all --tags'
        else:
            cmd = 'git clone --bare {source_url} {git_dir}'
        cmd = info.format(cmd , git_dir=git_dir.abspath())
        return exec_command(task, cmd)
    info.task('download',
              rule = clone_or_update,
              source = info.source_urlfile,
              target = git_dir)

    def checkout(task):
        pat = 'git --git-dir={git_dir} archive'
        pat += ' --format=tar --prefix={package}-{version}/ '
        pat += ' ' + getattr(info, 'vcs_tag', 'HEAD') # git tag, branch or hash
        pat += ' | tar -xvf -'
        cmd = info.format(pat, git_dir=git_dir.abspath())
        return exec_command(task, cmd)
    info.task('unpack',
              rule = checkout,
              source = git_dir,
              target = info.unpacked_target)
    

@feature('vcs', **requirements)
def feature_vcs(info):
    '''
    Handle source in a version controlled system.  

    This feature implements steps seturl, download and unpack with a
    result compatible with the "tarball" feature.
    '''

    flavor = info.vcs_flavor
    if not flavor:
        msg = info.format('VCS feature requested but no VCS flavor given for package {package}')
        info.error(msg)
        raise ValueError(msg)

    # make a file holding the repository URL.  This is just to prime
    # the dependency chain.
    info.debug('VCS: urlfile: %s %s --> %s' % (info.package, info.source_url, info.source_urlfile))
    def create_urlfile(task):
        tgt = task.outputs[0]
        tgt.write(info.format('{source_url}'))
        return 0
    info.task('seturl',
              rule = create_urlfile,
              update_outputs = True,
              target = info.source_urlfile,)

    # do checkout/clone into download area
    # def checkout_task(task):
    #     meth = eval('do_%s' % flavor)
    #     cmd = meth(info)
    #     return exec_command(task, cmd)
    # rule = rule_maker(info)
    # info.task('unpack',
    #           rule = rule,
    #           source = info.source_urlfile,
    #           target = info.unpacked_target,
    #           )
    

    doer = eval('do_%s' % flavor)
    doer(info)
    return

