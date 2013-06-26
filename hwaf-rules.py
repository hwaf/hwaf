# -*- python -*-

# stdlib imports
import os
import os.path as osp
import sys

# waf imports ---
import waflib.Utils
import waflib.Logs as msg
import waflib.Configure
import waflib.Build
import waflib.Task
import waflib.Tools.ccroot
from waflib.Configure import conf
from waflib.TaskGen import feature, before_method, after_method, extension, after

_heptooldir = osp.dirname(osp.abspath(__file__))
# add this directory to sys.path to ease the loading of other hepwaf tools
if not _heptooldir in sys.path: sys.path.append(_heptooldir)

### ---------------------------------------------------------------------------
class symlink_tsk(waflib.Task.Task):
    """
    A task to install symlinks of binaries and libraries under the *build*
    install-area (to not require shaggy RPATH)
    this is needed e.g. for genconf and gencliddb.
    """
    color   = 'PINK'
    reentrant = True
    
    def run(self):
        import os
        try:
            os.remove(self.outputs[0].abspath())
        except OSError:
            pass
        return os.symlink(self.inputs[0].abspath(),
                          self.outputs[0].abspath())


@feature('symlink_tsk')
@after_method('apply_link')
def add_install_copy(self):
    link_cls_name = self.link_task.__class__.__name__
    # FIXME: is there an API for this ?
    if link_cls_name.endswith('lib'):
        outdir = self.bld.path.make_node('.install_area').make_node('lib')
    else:
        outdir = self.bld.path.make_node('.install_area').make_node('bin')
    link_outputs = waflib.Utils.to_list(self.link_task.outputs)
    for out in link_outputs:
        if isinstance(out, str):
            n = out
        else:
            n = out.name
        out_sym = outdir.find_or_declare(n)
        #print("===> ", self.target, link_cls_name, out_sym.abspath())
        tsk = self.create_task('symlink_tsk',
                               out,
                               out_sym)
        self.source += tsk.outputs
        pass
    return

## EOF ##
