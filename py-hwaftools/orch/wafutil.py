#!/usr/bin/env python
'''
Utility functions needing waf
'''
import os
import os.path as osp
import waflib.Logs as msg
from waflib.Errors import WafError
import pprint

from . import util

def exec_command(task, cmd, **kw):
    '''
    helper function to:
     - run a command
     - log stderr and stdout into worch_<taskname>.log.txt
     - printout the content of that file when the command fails
    '''
    bld = task.generator.bld
    cwd = getattr(task, 'cwd', bld.out_dir)
    msg.debug('orch: exec command: %s: "%s" in %s' % (task.name, cmd, cwd))
    if not osp.exists(cwd):
        os.makedirs(cwd)

    log_dir = bld.root.make_node(osp.join(bld.out_dir, 'logs'))
    log_dir.mkdir()
    fnode = log_dir.make_node('worch_%s.log.txt' % task.name)
    flog = open(fnode.abspath(), 'w')

    cmd_dict = dict(kw)
    env = kw.get('env', task.env.env)
    cmd_dict.update({
        'cwd': cwd,
        'env': env, 
        'stdout': flog,
        'stderr': flog,
        })

    try:
        pdict = bld.env['orch_package_dict'][task.name.split('_',1)[0]]
    except KeyError:
        pdict = dict()

    flog.write('WORCH CMD: %s\n' % cmd)
    flog.write('WORCH CWD: %s\n' % cwd)
    flog.write('WORCH TSK: %s\n' % str(task))
    flog.write(pprint.pformat(task.__dict__, indent=2, depth=2))
    flog.write('\n')
    if pdict:
        flog.write('WORCH PKG:\n')
        flog.write(pprint.pformat(pdict, indent=2, depth=2))
    flog.write('\nWORCH ENV:\n\t%s' % \
                   '\n\t'.join(['%s = %s' % kv for kv in sorted(env.items())]))
    flog.write('\nWORCH command output:\n')
    flog.flush()

    try:
        ret = task.exec_command(cmd, **cmd_dict)
    except KeyboardInterrupt:
        raise
    except WafError:
        msg.error('Command failed with WafError: %s in %s' % (cmd, cwd))
        raise
    finally:
        flog.close()
    if msg.verbose and ret == 0 and 'orchstep' in msg.zones:
        with open(flog.abspath()) as f:
            msg.pprint('NORMAL','orchstep: %s (%s)\n%s' % \
                           (task.name, flog.name, ''.join(f.readlines())))
            pass
        pass
    if ret == 0:
        return 0
    msg.error('command failed with code %s, log in %s' % (ret, flog.name))
    repo = osp.join(cwd, "worch_%s.repo.sh" % task.name)
    with open(repo, 'w') as fp:
        fp.write('#!/bin/bash\n')
        fp.write('cd %s\n' % cwd)
        for var, val in sorted(env.items()):
            if val.startswith('()'):
                fp.write('%s %s\n' % (var, val))
            else:
                fp.write('export %s="%s"\n' % (var,val))
        fp.write('\n\n%s\n' % cmd)
    msg.error('reproduce with: %s' % repo)
    return ret


