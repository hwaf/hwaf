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
    ctx.load('hwaf-base', tooldir=_heptooldir)
    ctx.load('find_pthread', tooldir=_heptooldir)
    ctx.load('find_m', tooldir=_heptooldir)
    ctx.load('find_dl', tooldir=_heptooldir)
    ctx.load('find_z', tooldir=_heptooldir)
    ctx.load('find_rt', tooldir=_heptooldir)
    ctx.load('find_iberty', tooldir=_heptooldir)
    ctx.load('find_bfd', tooldir=_heptooldir)
    return

def configure(ctx):
    ctx.load('hwaf-base', tooldir=_heptooldir)
    ctx.load('find_pthread', tooldir=_heptooldir)
    ctx.load('find_m', tooldir=_heptooldir)
    ctx.load('find_dl', tooldir=_heptooldir)
    ctx.load('find_z', tooldir=_heptooldir)
    ctx.load('find_rt', tooldir=_heptooldir)
    ctx.load('find_iberty', tooldir=_heptooldir)
    ctx.load('find_bfd', tooldir=_heptooldir)
    return

@conf
def find_posixlibs(ctx, **kwargs):
    
    ctx.load('hwaf-base', tooldir=_heptooldir)

    if not ctx.env.HWAF_FOUND_C_COMPILER:
        ctx.fatal('load a C compiler first')
        pass

    # find libm
    libm_kw = dict(kwargs)
    libm_kw['mandatory'] = libm_kw.get('m_mandatory', False)
    ctx.find_m(**libm_kw)
    
    # find dl
    dl_kw = dict(kwargs)
    dl_kw['mandatory'] = dl_kw.get('dl_mandatory', False)
    ctx.find_dl(**dl_kw)

    # find pthread
    pthread_kw = dict(kwargs)
    pthread_kw['mandatory'] = pthread_kw.get('pthread_mandatory', False)
    ctx.find_pthread(**pthread_kw)

    # find libz
    libz_kw = dict(kwargs)
    libz_kw['mandatory'] = libz_kw.get('z_mandatory', False)
    ctx.find_z(**libz_kw)

    # find rt
    librt_kw = dict(kwargs)
    librt_kw['mandatory'] = librt_kw.get('rt_mandatory', False)
    ctx.find_rt(**librt_kw)

    # find libiberty
    iberty_kwargs = dict(kwargs)
    iberty_kwargs['mandatory'] = kwargs.get('iberty_mandatory', False)
    ctx.find_iberty(**iberty_kwargs)

    # find bfd
    bfd_kw = dict(kwargs)
    bfd_kw['mandatory'] = kwargs.get('bfd_mandatory', False)
    ctx.find_bfd(**bfd_kw)

    ctx.env.HWAF_FOUND_POSIXLIBS = 1
    return

## EOF ##
