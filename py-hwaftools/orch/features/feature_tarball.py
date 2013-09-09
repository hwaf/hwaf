#!/usr/bin/env python
from .pfi import feature

from orch.util import urlopen

def get_unpacker(filename, dirname):
    if filename.endswith('.zip'): 
        return 'unzip -d %s %s' % (dirname, filename)
    
    text2flags = {'.tar.gz':'xzf', '.tgz':'xzf', '.tar.bz2':'xjf', '.tar':'xf' }
    for ext, flags in text2flags.items():
        if filename.endswith(ext):
            return 'tar -C %s -%s %s' % (dirname, flags, filename)
    return 'tar -C %s -xf %s' % (dirname, filename)

requirements = {
    'source_urlfile': None,
    'source_url': None,
    'source_archive_checksum': None, # md5:xxxxx, sha224:xxxx, sha256:xxxx, ...
    'source_archive_ext': None,
    'source_archive_file': None,
    'download_dir': None,
    'source_download_target': None,
    'source_dir': None,
    'source_unpacked': None,
    'unpacked_target': None,
}


@feature('tarball', **requirements)
def feature_tarball(info):
    '''
    Handle a tarball source.  Implements steps seturl, download and unpack
    '''

    #print ('source_url: "%s" -> urlfile: "%s"' % (info.source_url, info.source_urlfile))
    info.task('seturl',
             rule = "echo '%s' > ${TGT}" % info.source_url, 
             update_outputs = True,
             target = info.source_urlfile)

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
            info.fatal("[{package_}_download] problem downloading [{source_url}]")

        checksum = info.source_archive_checksum
        if not checksum:
            return
        hasher_name, ref = checksum.split(":")
        import hashlib
        # FIXME: check the hasher method exists. check for typos.
        hasher = getattr(hashlib, hasher_name)()
        hasher.update(tgt.read('rb'))
        data= hasher.hexdigest()
        if data != ref:
            info.fatal("[{pacakge}_download] invalid MD5 checksum:\nref: %s\nnew: %s", ref, data)

        return

    info.task('download',
              rule = dl_task,
              source = info.source_urlfile, 
              target = info.source_archive_file)


    info.task('unpack',
              rule = get_unpacker(info.source_archive_file.abspath(), 
                                  info.source_dir.abspath()),
              source = info.source_archive_file, 
              target = info.unpacked_target)

    return
