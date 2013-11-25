#!/usr/bin/env python
'''
Features to produce a source directory from an online tar/zip archive.

It requires no previous steps.  It provides the 'seturl', 'download' and 'unpack' steps.
'''

from waflib.TaskGen import feature
import waflib.Logs as msg

from orch.util import urlopen, get_unpacker
from orch.wafutil import exec_command

import orch.features
orch.features.register_defaults(
    'tarball', 
    source_urlfile = '{urlfile_dir}/{package}-{version}.url',
    source_archive_ext = 'tar.gz',
    source_archive_file = '{source_unpacked}.{source_archive_ext}',
    source_archive_path = '{download_dir}/{source_archive_file}',
    source_archive_checksum = '',
    source_unpacked = '{package}-{version}',
    source_unpacked_path = '{source_dir}/{source_unpacked}',
    unpacked_target = 'README-{package}',
    source_unpacked_target = '{source_unpacked_path}/{unpacked_target}',
)

@feature('tarball')
def feature_tarball(tgen):
    '''
    Handle a tarball source.  Implements steps seturl, download and unpack
    '''

    #print ('source_url: "%s" -> urlfile: "%s"' % (info.source_url, info.source_urlfile))
    tgen.step('seturl',
              rule = "echo '%s' > %s" % (tgen.worch.source_url, tgen.worch.source_urlfile),
              update_outputs = True,
              target = tgen.worch.source_urlfile)

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
            msg.error(tgen.worch.format("[{package}_download] problem downloading [{source_url}]"))
            raise

        checksum = tgen.worch.source_archive_checksum
        if not checksum:
            return
        hasher_name, ref = checksum.split(":")
        import hashlib, os
        # FIXME: check the hasher method exists. check for typos.
        hasher = getattr(hashlib, hasher_name)()
        hasher.update(tgt.read('rb'))
        data= hasher.hexdigest()
        if data != ref:
            msg.error(tgen.worch.format("[{package}_download] invalid checksum:\nref: %s\nnew: %s" %\
                                        (ref, data)))
            try:
                os.remove(tgt.abspath())
            except IOError: 
                pass
            return 1
        return

    tgen.step('download',
              rule = dl_task,
              source = tgen.worch.source_urlfile, 
              target = tgen.worch.source_archive_path)


    def unpack_task(task):
        cmd = get_unpacker(task.inputs[0].abspath())
        return exec_command(task, cmd)

    tgen.step('unpack',
              rule = unpack_task,
              source = tgen.worch.source_archive_path, 
              target = tgen.worch.source_unpacked_target)

    return
