#!/usr/bin/env python
'''A "tarball"-like feature to which pulls from a VCS instead.  It
provides the "seturl" and "unpack" steps.  There is no "download" step
like "tarball" as the checkout/clone is direct to the source
directory.

'''
import os.path as osp
from waflib.TaskGen import feature
import waflib.Logs as msg

from orch.util import urlopen, get_unpacker
from orch.wafutil import exec_command

import orch.features
orch.features.register_defaults(
    'vcs', 
    source_urlfile = '{urlfile_dir}/{package}-{version}.url',
    source_unpacked = '{package}-{version}',
    source_unpacked_path = '{source_dir}/{source_unpacked}',
    unpacked_target = 'README',
    source_unpacked_target = '{source_unpacked_path}/{unpacked_target}',

    vcs_flavor = 'git',         # git,hg,svn,cvs 
    vcs_tag = '',
    vcs_module = '',            # used by cvs
)

def single_cmd_rule(func):
    def rule(tgen):
        def task_func(task):
            cmd = func(tgen)
            return exec_command(task, cmd)
        tgen.step('unpack',
                  rule = task_func,
                  source = tgen.worch.source_urlfile,
                  target = tgen.worch.source_unpacked_target)
    return rule

@single_cmd_rule
def do_cvs(tgen):
    tag = tgen.worch.get('vcs_tag', '')
    if tag:
        tag = '-r ' + tag
    module = tgen.worch.get('vcs_module', '')
    if not module:
        module = tgen.worch.package
    pat = 'cvs -d {source_url} checkout {vcs_tag_opt} -d {source_unpacked} {module}'
    return tgen.worch.format(pat, vcs_tag_opt=tag, module=module)

@single_cmd_rule
def do_svn(tgen):
    if tgen.worch.get('vcs_tag'):
        err = tgen.worch.format('SVN has no concept of tags, can not honor: "{vcs_tag}"')
        msg.error(err)
        raise ValueError(err)
    pat = "svn checkout {source_url} {source_unpacked}"
    return tgen.worch.format(pat)


@single_cmd_rule
def do_hg(tgen):
    tag = tgen.worch.get('vcs_tag', '')
    if tag:
        tag = '-b ' + tag
    pat = "hg clone {vcs_tag_opt} {source_url} {source_unpacked}"
    return tgen.worch.format(pat, vcs_tag_opt=tag)



def do_git(tgen):

    git_dir = tgen.make_node(tgen.worch.format('{download_dir}/{package}.git'))

    if osp.exists(git_dir.abspath()):
        clone_or_update = 'git --git-dir={git_dir} fetch --all --tags'
    else:
        clone_or_update = 'git clone --bare {source_url} {git_dir}'
    clone_or_update = tgen.worch.format(clone_or_update , git_dir=git_dir.abspath())
    tgen.step('download',
              rule = clone_or_update,
              source = tgen.worch.source_urlfile,
              target = git_dir)

    checkout = 'git --git-dir={git_dir} archive'
    checkout += ' --format=tar --prefix={package}-{version}/ '
    checkout += ' ' + getattr(tgen.worch, 'vcs_tag', 'HEAD') # git tag, branch or hash
    checkout += ' | tar -xvf -'
    checkout = tgen.worch.format(checkout, git_dir=git_dir.abspath())
    tgen.step('unpack',
              rule = checkout,
              source = tgen.control_node('download'),
              target = tgen.worch.source_unpacked_target)
    


@feature('vcs')
def feature_vcs(tgen):

    tgen.step('seturl', 
              rule = "echo '%s' > %s" % (tgen.worch.source_url, tgen.worch.source_urlfile),
              update_outputs = True,
              target = tgen.worch.source_urlfile)

    flavor = tgen.worch.vcs_flavor
    doer = eval('do_%s' % flavor)
    doer(tgen)
    return
    
    
