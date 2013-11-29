#!/usr/bin/env python
'''
Features to apply a patch to an unpacked source directory.

It requires the 'unpack' step and provides the 'patch' step.
'''
from waflib.TaskGen import feature
import waflib.Logs as msg

from orch.util import urlopen, get_unpacker
from orch.wafutil import exec_command

import orch.features
orch.features.register_defaults(
    'patch',
    patch_urlfile = '{urlfile_dir}/{package}-{version}.patch.url',
    patch_file = '{package}-{version}.patch',
    patch_file_path = '{patch_dir}/{patch_file}',
    patch_checksum = '',
    patch_cmd = 'patch -i',
    patch_cmd_std_opts = '',
    patch_cmd_options = '',
    )

@feature('patch')
def feature_patch(tgen):
    '''
    Apply a patch
    '''
    tgen.step('urlpatch',
              rule = "echo '%s' > %s" % (tgen.worch.patch_url, tgen.worch.patch_urlfile),
              update_outputs = True,
              target = tgen.worch.patch_urlfile)

    # fixme: this is mostly a cut-and-paste from feature_tarball.
    # Both should be factored out to common spot....
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
            msg.error(tgen.worch.format("[{package}_dlpatch] problem downloading [{patch_urlfile}]"))
            raise

        checksum = tgen.worch.patch_checksum
        if not checksum:
            return
        hasher_name, ref = checksum.split(":")
        import hashlib, os
        # FIXME: check the hasher method exists. check for typos.
        hasher = getattr(hashlib, hasher_name)()
        hasher.update(tgt.read('rb'))
        data= hasher.hexdigest()
        if data != ref:
            msg.error(tgen.worch.format("[{package}_dlpatch] invalid checksum:\nref: %s\nnew: %s" %\
                                        (ref, data)))
            try:
                os.remove(tgt.abspath())
            except IOError: 
                pass
            return 1
        return
    tgen.step('dlpatch',
              rule = dl_task,
              source = tgen.worch.patch_urlfile,
              target = tgen.worch.patch_file)

    def apply_patch(task):
        src = task.inputs[0].abspath()
        tgt = task.outputs[0].abspath()
        cmd = "%s %s %s" % ( tgen.worch.patch_cmd, src, tgen.worch.patch_cmd_options )
        ret = exec_command(task, cmd)
        return ret

    after =  tgen.worch.package + '_unpack'
    before = tgen.worch.package + '_prepare'

    tgen.step('patch',
              rule = apply_patch,
              source = [tgen.worch.patch_file, tgen.control_node('unpack')],
              target = [tgen.control_node('patch')],
              depends_on = [after],
              after = [after], before = [before])

    
