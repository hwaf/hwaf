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

def options(ctx):
    ctx.load('findbase', tooldir=_heptooldir)
    return

def configure(ctx):
    ctx.load('findbase platforms', tooldir=_heptooldir)
    return

@conf
def find_posixlibs(ctx, **kwargs):
    
    if not ctx.env.CC or not ctx.env.CXX:
        msg.fatal('load a C or C++ compiler first')
        pass

    ctx.load('findbase platforms', tooldir=_heptooldir)

    kwargs = ctx._findbase_setup(kwargs)
    
    kwargs['mandatory'] = True
    
    # find libm
    ctx.check_with(
        ctx.check,
        "m",
        features='cxx cxxprogram',
        lib='m',
        uselib_store='m',
        **kwargs
        )

    # find dl
    ctx.check_with(
        ctx.check,
        "dl",
        features='cxx cxxprogram',
        lib='dl',
        uselib_store='dl',
        **kwargs
        )

    # find pthread
    ctx.check_with(
        ctx.check,
        "pthread",
        features='cxx cxxprogram',
        lib='pthread',
        uselib_store='pthread',
        **kwargs
        )

    # find libz
    ctx.check_with(
        ctx.check,
        "zlib",
        features='cxx cxxprogram',
        header_name="zlib.h",
        lib='z',
        uselib_store='z',
        **kwargs
        )

    # find bfd
    # first find the library
    ctx.check_with(
        ctx.check,
        "bfd",
        features='cxx cxxprogram',
        lib='bfd',
        uselib_store='bfd',
        **kwargs
        )
    # then the header
    ctx.check_with(
        ctx.check,
        "bfd",
        features='cxx cxxprogram',
        header_name="bfd.h",
        lib='bfd',
        uselib_store='bfd',
        use='bfd',
        **kwargs
        )

    # find rt
    if not ctx.is_darwin():
        ctx.check_with(
            ctx.check,
            "rt",
            features='cxx cxxprogram',
            lib='rt',
            uselib_store='rt',
            **kwargs
            )
        pass

    ctx.env.HEPWAF_FOUND_POSIXLIBS = 1
    return

## EOF ##
