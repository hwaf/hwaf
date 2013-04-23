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
        '--with-gccxml',
        default=None,
        help="Look for GCCXML at the given path")
    return

def configure(conf):
    conf.load('hwaf-base', tooldir=_heptooldir)
    return

@conf
def find_gccxml(ctx, **kwargs):
    
    if not ctx.env.HWAF_FOUND_C_COMPILER:
        ctx.fatal('load a C compiler first')
        pass

    if not ctx.env.HWAF_FOUND_CXX_COMPILER:
        ctx.fatal('load a C++ compiler first')
        pass


    # find gccxml
    gccxml_bin = "gccxml"
    path_list = []
    if getattr(ctx.options, 'with_gccxml', None):
        topdir = ctx.options.with_gccxml
        topdir = waflib.Utils.subst_vars(topdir, ctx.env)

        gccxml_bin = osp.join(topdir, "bin", "gccxml")
        path_list.append(osp.join(topdir, "bin"))
        pass
    kwargs['path_list']=path_list
    
    ctx.find_program(
        gccxml_bin,
        var="GCCXML",
        **kwargs)
    gccxml_bin = ctx.env['GCCXML']
    
    version="N/A"
    cmd = [ctx.env.GCCXML, "--version"]
    lines=ctx.cmd_and_log(cmd).splitlines()
    for l in lines:
        l = l.lower()
        if "version" in l:
            version=l[l.find("version")+len("version"):].strip()
            break
        pass
    ctx.start_msg("GCCXML version")
    ctx.end_msg(version)

    ctx.env.GCCXML_VERSION = version
    ctx.env.GCCXML_BINDIR = osp.dirname(ctx.env.GCCXML)
    ctx.env.GCCXML_HOME = osp.dirname(ctx.env.GCCXML_BINDIR)
    
    ctx.declare_runtime_env('GCCXML')
    ctx.declare_runtime_env('GCCXML_BINDIR')

    ctx.env.HWAF_FOUND_GCCXML = 1
    return

## EOF ##
