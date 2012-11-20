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

    opt.load('hep-waftools-base', tooldir=_heptooldir)

    opt.add_option(
        '--with-gccxml',
        default=None,
        help="Look for GCCXML at the given path")
    return

def configure(conf):
    conf.load('hep-waftools-base', tooldir=_heptooldir)
    return

@conf
def find_gccxml(ctx, **kwargs):
    
    if not ctx.env.CXX:
        msg.fatal('load a C++ compiler first')
        pass


    path_list = []
    if ctx.options.with_gccxml:
        path_list.append(
            osp.join(ctx.options.with_gccxml, "bin")
            )
        pass

    ctx.find_program(
        "gccxml",
        var="GCCXML",
        path_list=path_list,
        **kwargs)
    
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

    ctx.declare_runtime_env('GCCXML')
    ctx.declare_runtime_env('GCCXML_BINDIR')

    ctx.env.HEPWAF_FOUND_GCCXML = 1
    return

## EOF ##
