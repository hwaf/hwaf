#!/usr/bin/env python
from .pfi import feature
from orch.util import urlopen

from orch.wafutil import exec_command

requirements = {
    'unpacked_target': None,
    'patch_urlfile': None,
    'patch_url': None,
    'patch_file': None,
    'patch_cmd': 'patch -i',    # append abspath to patch file
    'patch_cmd_options': '',    # appends to patch_cmd
    'patch_target': None,
}


@feature('patch', **requirements)
def feature_patch(info):
    '''
    Apply a patch on the unpacked sources.
    '''
    if not info.patch_url:
        return

    info.task('urlpatch',
              rule = "echo %s > ${TGT}" % info.patch_url,
              update_outputs = True,
              source = info.unpacked_target,
              target = info.patch_urlfile,
              depends_on = info.format('{package}_unpack'))

    def dl_task(task):
        src = task.inputs[0]
        tgt = task.outputs[0]
        url = src.read().strip()
        try:
            web = urlopen(url)
            tgt.write(web.read(),'wb')
        except Exception:
            import traceback
            traceback.print_exc()
            info.ctx.fatal("[%s] problem downloading [%s]" % (info.format('{package}_dlpatch'), url))

    info.task('dlpatch',
             rule = dl_task,
             source = info.patch_urlfile,
             target = info.patch_file)

    def apply_patch(task):
        src = task.inputs[0].abspath()
        tgt = task.outputs[0].abspath()
        cmd = "%s %s %s" % ( info.patch_cmd, src, info.patch_cmd_options )
        ret = exec_command(task, cmd)
        if ret != 0:
            return ret
        cmd = "touch %s" % tgt
        ret = task.exec_command(cmd)
        return ret

    info.task('patch',
             rule = apply_patch,
             source = info.patch_file,
             target = info.patch_target)


    info.dependency(info.format('{package}_patch'),
                    info.format('{package}_prepare'))
    return
