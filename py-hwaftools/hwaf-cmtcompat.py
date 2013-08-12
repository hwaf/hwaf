# -*- python -*-

# stdlib imports
import os
import os.path as osp
import sys

# waf imports ---
import waflib.Options
import waflib.Utils
import waflib.Logs as msg
from waflib.Configure import conf

_heptooldir = osp.dirname(osp.abspath(__file__))
# add this directory to sys.path to ease the loading of other hepwaf tools
if not _heptooldir in sys.path: sys.path.append(_heptooldir)

### ---------------------------------------------------------------------------
@conf
def _cmt_get_srcs_lst(self, source, root=None):
    '''hack to support implicit src/*cxx in CMT req-files'''
    if root is None:
        root = self.path
    if isinstance(source, (list, tuple)):
        src = []
        for s in source:
            src.extend(self._cmt_get_srcs_lst(s, root=root))
        return src
    elif not isinstance(source, type('')):
        ## a waflib.Node ?
        return [source]
    else:
        src_node = root.find_dir('src')
        srcs = root.ant_glob(source)
        if srcs:
            # OK. finders, keepers.
            pass
        elif src_node:
            # hack to mimick CMT's default (to take sources from src)
            srcs = src_node.ant_glob(source)
            pass
        if not srcs:
            # ok, try again from bldnode
            src_node = root.find_dir('src')
            try:             srcs = root.get_bld().ant_glob(source)
            except OSError:  srcs = None
            if srcs:
                # OK. finders, keepers.
                pass
            elif src_node:
                # hack to mimick CMT's default (to take sources from src)
                try:            srcs = src_node.get_bld().ant_glob(source)
                except OSError: srcs = root.ant_glob(source)
                pass
            if not srcs:
                # ok, maybe the output of a not-yet executed task
                srcs = source
                pass
            pass
        return waflib.Utils.to_list(srcs)
    self.fatal("unreachable")
    return []
