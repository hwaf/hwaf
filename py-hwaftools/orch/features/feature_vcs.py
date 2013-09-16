#!/usr/bin/env python
'''
The VCS feature downloads and unpacks a source archive stored in a
version control system.  It is a drop-in replacement for the "tarball"
feature but does not make use of any intermediate downloaded files.
Its final step is "unpack".
'''

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

# all three flavors 
def make_cloner(flavor):
    def cloner(info):
        flavor = info.vcs_flavor

        command = 'clone'
        if flavor in ['svn']:
            command = 'checkout'
        
        tag = info.vcs_tag
        if tag:
            if flavor in ['svn']:
                info.warn('SVN has no concept of tags, ignoring tag: "{vcs_tag}"')
                tag = ''
            else:
                tag = '-b ' + tag # both git and hg

        pat = "{vcs_flavor} {vcs_command} {vcs_tag_opt} {source_url} {source_unpacked}"
        return info.format(pat, vcs_tag_opt=tag, vcs_command = command)
    return cloner

def cvser(info):
    '''
    Return a cvs checkout command
    '''
    tag = info.vcs_tag or ''
    if tag:
        tag = '-r ' + tag
    module = info.vcs_module or ''
    if not module:
        module = info.package

    pat = '{vcs_flavor} -d {source_url} checkout {vcs_tag_opt} -d {source_unpacked} {module}'
    return info.format(pat, vcs_tag_opt=tag, module=module)

vcs_commands = dict(
    cvs = cvser,
    git = make_cloner('git'),
    hg = make_cloner('hg'),
    svn = make_cloner('svn'),
    )


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
    def checkout_task(task):
        cmd = vcs_commands[flavor](info)
        return exec_command(task, cmd)
    info.task('unpack',
              rule = checkout_task,
              source = info.source_urlfile,
              target = info.unpacked_target,
              )
    
    return

