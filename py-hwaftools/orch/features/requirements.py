#!/usr/bin/env python
'''Feature requirements

This module provides the .pool data member which is a dictionary keyed
by configuration item keys.  The values are named tuples holding
information about the key.  this information is:

 - name
 - default value
 - brief documentation

Other configuration items may be defined but only those in the pool
are directly referenced by the features.

'''

from collections import namedtuple

def ReqDesc(name, value, relative = None, typecode = 's', doc = None):
    '''
    Return a requirements description item

    - name :: the name of the corresponding configuration key

    - value :: the value (subject to interpolation)

    - relative :: the name of another ReqDesc (of type directory) to serve as a parent node

    - typecode :: what the quantity is [s]tring, [f]ile or [d]irectory

    - doc :: a brief documentation string
    '''
    if not doc:
        doc = 'Requirement "%s" with value "%s"' % (name, value)
    else:
        doc += ' (value: "%s")' % value
    return namedtuple('ReqDesc','name value relative typecode doc')(name, value, relative, typecode, doc)


# Every valid feature must use zero or more requirements from this
# list.  When introducing a new feature, add or reuse existing
# requirements.  Keep in mind which features must coexist for any
# given package in order to keep the names distinct.  

reqdesc_list = [
    # general
    ReqDesc('package', None,
            doc='name of the package'),
    ReqDesc('version', None,
            doc='version string of the package'),
    ReqDesc('tags','',
            doc='A list of asserted tags to drive features in optional manners'),
    

    # locations
    ReqDesc('urlfile_dir', 'urlfiles', typecode='d', 
            doc='where to store URL files'),
    ReqDesc('download_dir', 'downloads', typecode='d', 
            doc='where to store download files'),
    ReqDesc('source_dir', 'sources', typecode='d', 
            doc='where to unpack source archives, w.r.t. OUT'),
    ReqDesc('patchfile_dir','patchfiles', typecode='d',
            doc='where to store patch files'),
    ReqDesc('build_dir', 'builds/{package}-{version}-{tagsdashed}', typecode='d',
            doc='base of where to build'),
    ReqDesc('install_dir', '{PREFIX}/{package}/{version}/{tagsdashed}', typecode='d',
            doc='base of where to install'),
    ReqDesc('dest_install_dir', '{DESTDIR}{install_dir}', typecode='d',
            doc='directory where to stage install artifacts'),

    # package source archive related
    ReqDesc('source_url', None,
            doc='the URL pointing at the source archive'),
    ReqDesc('source_urlfile', '{package}-{version}.url', typecode='f', relative='{urlfile_dir}',
            doc='file holding the URL of the source package'),
    # default here assumes tarball feature
    ReqDesc('source_archive_file','{package}-{version}.{source_archive_ext}', typecode='f', relative='{download_dir}',
            doc='The file name of the source archive'),
    ReqDesc('source_download_target','{source_archive_file}', typecode='f', relative='{download_dir}',
            doc='The file produced by a successful download'),
    ReqDesc('source_unpacked', '{package}-{version}', typecode='d', relative='{source_dir}',
            doc='unpacked source directory'),
    ReqDesc('unpacked_target','README', typecode='f', relative='{source_dir}/{source_unpacked}',
            doc='A file which indicates successful unpacking'),

    # source archive files, package sources in the form of a single archive file (tar/zip)
    ReqDesc('source_archive_checksum', '', 
            doc='expected checksum of source archive file prefixed with hash type (eg "md5:")'),
    ReqDesc('source_archive_ext', 'tar.gz',
            doc='source archive file extension'),

    # patching sources, the patch command is run from inside the source_unpacked directory
    ReqDesc('patch_urlfile','{package}-{version}.patch.url', typecode='f', relative='{urlfile_dir}',
            doc='The file holding the URL of the patch file'),
    ReqDesc('patch_url', None,  # user must supply
            doc='The URL of the patch file'),
    ReqDesc('patch_file','{package}-{version}.patch', typecode='f', relative='{patchfile_dir}',
            doc='The patch file to apply'),
    ReqDesc('patch_cmd', None,  # patching feature should supply
            doc='The patch command, the patch file will be appended'),
    ReqDesc('patch_cmd_options',None,
            doc='Patch command options, appended to patch command + patch file'),
    ReqDesc('patch_target','{package}-{version}.applied', typecode='f', relative='{patchfile_dir}',
            doc='A file indicating a successful application of the patch'),

    # source preparation (autoconf/cmake)
    ReqDesc('prepare_cmd', None, 
            doc='Command to prepare the source for building'),
    ReqDesc('prepare_cmd_options', '',
            doc='Options for the prepare command'),
    ReqDesc('prepare_target', None, typecode='f', relative='{build_dir}',
            doc='File that is produced upon successful completion of preparation'),

    # building (makemake)
    ReqDesc('build_cmd', None, 
            doc='Command to build the source'),
    ReqDesc('build_cmd_options', '',
            doc='Options for the build command'),
    ReqDesc('build_target', None, typecode='f', relative='{build_dir}',
            doc='File that is produced upon successful completion of building'),

    # installing (makemake)
    ReqDesc('install_cmd', None, 
            doc='Command to install the built package'),
    ReqDesc('install_cmd_options', '',
            doc='Options for the build command'),
    ReqDesc('install_target', None, typecode='f', relative='{dest_install_dir}',
            doc='File that is produced upon successful installation'),

    ]


def make_pool():
    #return {x.name:x for x in reqdesc_list}
    # no dict comprehension in Python 2.6
    ret = dict()
    for x in reqdesc_list:
        ret[x.name] = x
    return ret

pool = make_pool()
    
def valuedict():
    #return {x.name:x.value for x in reqdesc_list}
    ret = dict()
    for x in reqdesc_list:
        ret[x.name] = x.value
    return ret


def select(reqs):
    '''
    Return a subset of the pool with the keys in <reqs>.

    The returned req will have its value replaced if the <reqs> value is non None.
    '''
    req_keys = set(reqs.keys())
    all_keys = set(pool.keys())

    if not req_keys.issubset(all_keys):
        raise ValueError(
            'Unknown requirements: %s' %
            ', '.join(req_keys.difference(all_keys))
            )

    ret = dict()
    for pkey,preq in pool.items():
        val = reqs.get(pkey)
        if val is None:         # feature requirements lack or don't specify
            ret[pkey] = preq    # so, take pool default
            continue

        # Take feature default instead of pool default
        ret[pkey] = preq._replace(value=val)
    return ret


