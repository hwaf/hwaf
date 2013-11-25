#!/usr/bin/env python

from waflib.TaskGen import feature
import waflib.Logs as msg

import orch.features
orch.features.register_defaults('dumpenv', dumpenv_cmd = 'env')

@feature('dumpenv')
def feature_dumpenv(tgen):
    '''
    Dump the environment
    '''
    msg.debug('orch: dumping environment')
    tgen.worch_hello()
    tgen.step('dumpenv', rule = tgen.worch.format("{dumpenv_cmd}|egrep 'PWD|FOO|BAR'"))

