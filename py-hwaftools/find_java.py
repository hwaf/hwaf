# -*- python -*-

# stdlib imports ---
import os
import os.path as osp

# waf imports ---
import waflib.Utils
import waflib.Logs as msg
from waflib.Configure import conf

#
_heptooldir = osp.dirname(osp.abspath(__file__))

def options(opt):
    opt.load('hwaf-base', tooldir=_heptooldir)
    opt.add_option(
        '--with-java',
        default=None,
        help="Look for JAVA at the given path")
    return

def configure(conf):
    conf.load('hwaf-base', tooldir=_heptooldir)
    return

@conf
def find_java(ctx, **kwargs):
    
    # find java
    path_list = waflib.Utils.to_list(kwargs.get('path_list', []))
    if getattr(ctx.options, 'with_java', None):
        topdir = ctx.options.with_java
        topdir = ctx.hwaf_subst_vars(topdir)
        path_list.append(osp.join(topdir, "bin"))
        ctx.env.prepend_value('PATH', path_list)
        pass

    ctx.environ = ctx._hwaf_get_runtime_env()
    if ctx.env['JAVA_HOME']:
        ctx.environ['JAVA_HOME'] = ctx.env.get_flat('JAVA_HOME')
        pass
    ctx.load('java')
        
    ctx.env.HWAF_FOUND_JAVA = 1
    return

## EOF ##
