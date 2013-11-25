#!/usr/bin/env python
'''
Features to download a file.

It requires no previous steps.  It provides the 'download_seturl' and
'download' steps
'''

from waflib.TaskGen import feature
import waflib.Logs as msg

from orch.util import urlopen

import orch.features
orch.features.register_defaults(
    'dlrun', 
    dlrun_urlfile = '{package}-{version}.url',
    dlrun_url = None,
    dlrun_target = None,
    dlrun_checksum = '',
    dlrun_dir = '.',
    dlrun_cmd_options = '',
    dlrun_cmd_target = None,
)

@feature('dlrun')
def feature_dlrun(tgen):
    '''
    Download a file.
    '''
    work_dir = tgen.make_node(tgen.worch.dlrun_dir)

    tgen.step('dlrun_seturl',
              rule = "echo '%s' > %s" % (tgen.worch.dlrun_url,
                                         tgen.worch.dlrun_urlfile),
              update_outputs = True,
              target = tgen.worch.dlrun_urlfile)

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
            msg.error(tgen.worch.format("error downloading {dlrun_url}"))
            raise

        checksum = tgen.worch.dlrun_checksum
        if not checksum:
            return
        hasher_name, ref = checksum.split(":")
        import hashlib, os
        # FIXME: check the hasher method exists. check for typos.
        hasher = getattr(hashlib, hasher_name)()
        hasher.update(tgt.read('rb'))
        data= hasher.hexdigest()
        if data != ref:
            msg.error(tgen.worch.format("invalid checksum:\nref: %s\nnew: %s" %\
                                            (ref, data)))
            try:
                os.remove(tgt.abspath())
            except IOError: 
                pass
            return 1
        return

    script = work_dir.make_node(tgen.worch.dlrun_target)
    tgen.step('dldownload',
              rule = dl_task,
              source = tgen.worch.dlrun_urlfile, 
              target = script,
              cwd = work_dir.abspath())

    cmd_rule = tgen.worch.format('chmod +x {dlrun_cmd} && ./{dlrun_cmd} {dlrun_cmd_options}')
    tgen.step('dlcommand',
              rule = cmd_rule,
              source = script,
              target = map(work_dir.make_node, tgen.to_list(tgen.worch.dlrun_cmd_target)),
              cwd = work_dir.abspath())
    return
