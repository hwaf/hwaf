#!/usr/bin/env python

from .pfi import feature

requirements = {
    'dumpenv_cmd': None,
}

@feature('dumpenv', **requirements)
def feature_dumpenv(info):
    '''
    Dump the environment
    '''
    info.task('dumpenv', rule = info.dumpenv_cmd)
