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
# monkey patch waflib.ConfigSet.ConfigSet to log environment mods
if 1:
    import traceback
    import waflib.ConfigSet
    _orig_ConfigSet_setitem = waflib.ConfigSet.ConfigSet.__setitem__
    _orig_ConfigSet_setattr = waflib.ConfigSet.ConfigSet.__setattr__
    _orig_ConfigSet_append_value = waflib.ConfigSet.ConfigSet.append_value
    _orig_ConfigSet_prepend_value = waflib.ConfigSet.ConfigSet.prepend_value
    _orig_ConfigSet_append_unique = waflib.ConfigSet.ConfigSet.append_unique

    def _tb_stack_filter(stack):
        '''keep a
        '''
        who = stack[-1]
        fname = who[0]
        if fname.endswith(('waflib/Configure.py',
                           'waflib/ConfigSet.py',
                           'share/hwaf/tools/hwaf-base.py',
                           'tools/hwaf-base.py',
                           'share/hwaf/tools/hwaf-spy-env.py',
                           'tools/hwaf-spy-env.py',
                           )):
            return True
        return False
    
    mylog = open('spy.log.txt', 'w')
    def _new_ConfigSet_setitem(self, key, value):
        if key == 'HWAF_ENV_SPY':
            return _orig_ConfigSet_setitem(self, key, value)
        
        stack = traceback.extract_stack()[:-1]
        if _tb_stack_filter(stack):
            return _orig_ConfigSet_setitem(self, key, value)
            
        print(">>> __setitem__(%s, %s)..." % (key, stack), file=mylog)
        mylog.flush()
        old_value = self[key]
        ret = _orig_ConfigSet_setitem(self, key, value)
        new_value = self[key]
        try:
            if old_value != new_value or 1:
                _orig_ConfigSet_append_value(
                    self,
                    'HWAF_ENV_SPY',
                    [{'action': 'set',
                      'key': key,
                      'old': old_value,
                      'new': new_value,
                      'val': value,
                      'who': stack[-1],
                      }]
                    )
        except Exception as err:
            print ("*** error: %s" % err)
            print (traceback.extract_stack())
        return ret
    waflib.ConfigSet.ConfigSet.__setitem__ = _new_ConfigSet_setitem

    def _new_ConfigSet_setattr(self, key, value):
        if key == 'HWAF_ENV_SPY':
            return _orig_ConfigSet_setattr(self, key, value)
        stack = traceback.extract_stack()[:-1]
        if _tb_stack_filter(stack):
            return _orig_ConfigSet_setattr(self, key, value)
        print(">>> __setattr__(%s, %s)..." % (key, stack), file=mylog)
        mylog.flush()
        old_value = self[key]
        ret = _orig_ConfigSet_setattr(self, key, value)
        new_value = self[key]
        try:
            if old_value != new_value or 1:
                _orig_ConfigSet_append_value(
                    self,
                    'HWAF_ENV_SPY',
                    [{'action': 'set',
                      'key': key,
                      'old': old_value,
                      'new': new_value,
                      'val': value,
                      'who': stack[-1],
                      }]
                    )
        except Exception as err:
            print ("*** error: %s" % err)
            print (traceback.extract_stack())
        return ret
    waflib.ConfigSet.ConfigSet.__setattr__ = _new_ConfigSet_setattr

    def _new_ConfigSet_append_value(self, var, val):
        if var == 'HWAF_ENV_SPY':
            return _orig_ConfigSet_append_value(self, var, val)
        stack = traceback.extract_stack()[:-1]
        if _tb_stack_filter(stack):
            return _orig_ConfigSet_append_value(self, var, val)
        
        print(">>> append_value(%s, %s)..." % (var, stack), file=mylog)
        mylog.flush()
        old_value = self[var]
        ret = _orig_ConfigSet_append_value(self, var, val)
        new_value = self[var]
        try:
            if old_value != new_value or 1:
                _orig_ConfigSet_append_value(
                    self,
                    'HWAF_ENV_SPY',
                    [{'action': 'append_value',
                      'key': var,
                      'old': old_value,
                      'new': new_value,
                      'val': val,
                      'who': stack[-1],
                      }]
                    )
        except Exception as err:
            print ("*** error: %s" % err)
            print (traceback.extract_stack())
        return ret
    waflib.ConfigSet.ConfigSet.append_value = _new_ConfigSet_append_value

    def _new_ConfigSet_prepend_value(self, var, val):
        if var == 'HWAF_ENV_SPY':
            return _orig_ConfigSet_prepend_value(self, var, val)
        stack = traceback.extract_stack()[:-1]
        if _tb_stack_filter(stack):
            return _orig_ConfigSet_prepend_value(self, var, val)
        
        print(">>> prepend_value(%s, %s)..." % (var, stack), file=mylog)
        mylog.flush()
        old_value = self[var]
        ret = _orig_ConfigSet_prepend_value(self, var, val)
        new_value = self[var]
        try:
            if old_value != new_value or 1:
                _orig_ConfigSet_append_value(
                    self,
                    'HWAF_ENV_SPY',
                    [{'action': 'prepend_value',
                      'key': var,
                      'old': old_value,
                      'new': new_value,
                      'val': val,
                      'who': stack[-1],
                      }]
                    )
        except Exception as err:
            print ("*** error: %s" % err)
            print (traceback.extract_stack())
        return ret
    waflib.ConfigSet.ConfigSet.prepend_value = _new_ConfigSet_prepend_value

    def _new_ConfigSet_append_unique(self, var, val):
        if var == 'HWAF_ENV_SPY':
            return _orig_ConfigSet_append_unique(self, var, val)
        stack = traceback.extract_stack()[:-1]
        if _tb_stack_filter(stack):
            return _orig_ConfigSet_append_unique(self, var, val)
        
        print(">>> append_unique(%s, %s)..." % (var, stack), file=mylog)
        mylog.flush()
        old_value = self[var]
        ret = _orig_ConfigSet_append_unique(self, var, val)
        new_value = self[var]
        try:
            if old_value != new_value or 1:
                _orig_ConfigSet_append_value(
                    self,
                    'HWAF_ENV_SPY',
                    [{'action': 'append_unique',
                      'key': var,
                      'old': old_value,
                      'new': new_value,
                      'val': val,
                      'who': stack[-1],
                      }]
                    )
        except Exception as err:
            print ("*** error: %s" % err)
            print (traceback.extract_stack())
        return ret
    waflib.ConfigSet.ConfigSet.append_unique = _new_ConfigSet_append_unique

    pass

## EOF ##
