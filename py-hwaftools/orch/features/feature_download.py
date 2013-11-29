#!/usr/bin/env python
'''
A feature to download a file.

It requires no previous steps.  It provides the 'download_seturl' and
'download' steps
'''

import os
from waflib.TaskGen import feature
import waflib.Logs as msg

from orch.util import urlopen

import orch.features
orch.features.register_defaults(
    'download', 
    download_urlfile = '{package}-{version}.url',
    download_url = None,
    download_checksum = '',
    download_target = None,
)

@feature('download')
def feature_download(tgen):
    '''
    Download a file.
    '''
    work_dir = tgen.make_node(tgen.worch.download_dir)
    target_filename = tgen.worch.download_target
    if not target_filename:
        target_filename = os.path.basename(tgen.worch.download_url)
    target_node = work_dir.make_node(target_filename)

    tgen.step('download_seturl',
              rule = "echo '%s' > %s" % (tgen.worch.download_url,
                                         tgen.worch.download_urlfile),
              update_outputs = True,
              target = tgen.worch.download_urlfile)

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
            msg.error(tgen.worch.format("error downloading {download_url}"))
            raise

        checksum = tgen.worch.download_checksum
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

    tgen.step('download',
              rule = dl_task,
              source = tgen.worch.download_urlfile, 
              target = target_node,
              cwd = work_dir.abspath())

    return
