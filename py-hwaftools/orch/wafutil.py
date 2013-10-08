#!/usr/bin/env python
'''
Utility functions needing waf
'''
import os
import os.path as osp
import waflib.Logs as msg

def exec_command(task, cmd, **kw):
    '''
    helper function to:
     - run a command
     - log stderr and stdout into worch_<taskname>.log.txt
     - printout the content of that file when the command fails
    '''
    cwd = getattr(task, 'cwd', task.generator.bld.out_dir)
    msg.debug('orch: exec command: %s: "%s" in %s' % (task.name, cmd, cwd))
    if not osp.exists(cwd):
        os.makedirs(cwd)
    flog = open(osp.join(cwd, "worch_%s.log.txt" % task.name), 'w')
    cmd_dict = dict(kw)
    env = kw.get('env', task.env.env)
    cmd_dict.update({
        'cwd': cwd,
        'env': env, 
        'stdout': flog,
        'stderr': flog,
        })
    flog.write('WORCH CMD: %s\n' % cmd)
    flog.write('WORCH CWD: %s\n' % cwd)
    flog.write('WORCH TSK: %s %s\n' % (type(task), str(task)))
    flog.write('\n\t%s' % \
               '\n\t' .join(['%s = %s' % kv for kv in sorted(task.__dict__.items())]))
    flog.write('\nWORCH ENV:\n\t%s' % \
                   '\n\t'.join(['%s = %s' % kv for kv in sorted(env.items())]))
    flog.write('\nWORCH command output:\n')
    flog.flush()

    try:
        ret = task.exec_command(cmd, **cmd_dict)
    except KeyboardInterrupt:
        raise
    finally:
        flog.close()
    if msg.verbose and ret == 0 and 'orch' in msg.zones:
        with open(flog.name) as f:
            msg.pprint('NORMAL','orch: %s (%s)\n%s' % \
                           (task.name, flog.name, ''.join(f.readlines())))
            pass
        pass
    if ret == 0:
        return 0
    msg.error('command failed with code %d, log in %s' % (ret, flog.name))
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
