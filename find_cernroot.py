# -*- python -*-

# stdlib imports ---
import os
import os.path as osp

# waf imports ---
import waflib.Utils
import waflib.Logs as msg
from waflib.Configure import conf

#

def options(ctx):

    ctx.load('compiler_c compiler_cxx python')
    ctx.load('findbase', tooldir="hep-waftools")

    ctx.add_option(
        '--with-root-sys',
        default=None,
        help="Look for CERN ROOT System at the given path")
    return

def configure(ctx):
    ctx.load('compiler_c compiler_cxx')
    ctx.load('findbase platforms', tooldir="hep-waftools")
    return

@conf
def find_cernroot(ctx, **kwargs):
    
    ctx.load('findbase platforms find_python', tooldir="hep-waftools")

    if not ctx.env.HEPWAF_FOUND_PYTHON:
        ctx.find_python(version=kwargs.get('python_version', (2,6)))
    
    if not ctx.env.CXX:
        msg.fatal('load a C++ compiler first')
        pass


    if not ctx.env.PYTHON:
        msg.fatal('load a python interpreter first')
        pass

    kwargs = ctx._findbase_setup(kwargs)
    
    # find root
    root_cfg = "root-config"
    if ctx.options.with_root_sys:
        root_cfg = osp.join(ctx.options.with_root_sys, "bin", "root-config")
        pass

    
    kwargs['mandatory'] = True
    
    ctx.find_program(root_cfg, var='ROOT-CONFIG',**kwargs)
    root_cfg = ctx.env['ROOT-CONFIG']
    
    ctx.check_cfg(
        path=root_cfg,
        package="",
        uselib_store="ROOT",
        args='--libs --cflags --ldflags',
        **kwargs)

    ctx.find_program('genmap',      var='GENMAP',     **kwargs)
    ctx.find_program('genreflex',   var='GENREFLEX',  **kwargs)
    ctx.find_program('root',        var='ROOT-EXE',   **kwargs)
    ctx.find_program('rootcint',    var='ROOTCINT',   **kwargs)

    # reflex...
    ctx.copy_uselib_defs(dst='Reflex', src='ROOT')
    ctx.env['LIB_Reflex'] = ['Reflex']
    
    # cintex...
    ctx.copy_uselib_defs(dst='Cintex', src='ROOT')
    ctx.env['LIB_Cintex'] = ['Reflex', 'Cintex']
    
    # pyroot...
    ctx.copy_uselib_defs(dst='PyROOT', src='ROOT')
    ctx.env['LIB_PyROOT'] = ['PyROOT'] + ctx.env['LIB_python']

     # XMLIO...
    ctx.copy_uselib_defs(dst='XMLIO', src='ROOT')
    ctx.env['LIB_XMLIO'] = ['XMLIO']

    # XMLParser
    ctx.copy_uselib_defs(dst='XMLParser', src='ROOT')
    ctx.env['LIB_XMLParser'] = ['XMLParser']

    #msg.start_msg

    # -- check everything is kosher...
    ctx.check_cxx(
        msg="Checking for ROOT::TH1",
        fragment='''\
        #include "TH1F.h"
        void test_th1f() { new TH1F("th1f", "th1f", 100, 0., 100.); }
        int main(int argc, char* argv[]) {
          test_th1f();
          return 0;
        }
        ''',
        use="ROOT",
        execute  = True,
        mandatory=True,
        )

    ctx.check_cxx(
        msg="Checking for ROOT::TTree",
        fragment='''\
        #include "TTree.h"
        void test_ttree() { new TTree("tree", "tree"); }
        int main(int argc, char* argv[]) {
          test_ttree();
          return 0;
        }
        ''',
        use="ROOT",
        execute  = True,
        mandatory=True,
        )

    ctx.check_cxx(
        msg="Checking for pyroot",
        features='cxx cxxshlib',
        fragment='''\
        #include "Python.h"
        #include "TPython.h"
        #include "TPyException.h"
        
        void throw_py_exception ()
        {
          throw PyROOT::TPyException();
        }
        ''',
        use="ROOT PyROOT python",
        mandatory=True,
        )

    ctx.check_cxx(
        msg="Checking for reflex",
        features='cxx cxxshlib',
        fragment='''\
        #include "Reflex/Type.h"
        #include <iostream>
        
        void check_reflex ()
        {
          std::cout << "typeof(int): ["
                    << Reflex::Type::ByName("int").Name()
                    << std::endl;
        }
        ''',
        use="ROOT Reflex",
        mandatory=True,
        )

    ctx.check_cxx(
        msg="Checking for cintex",
        fragment='''\
        #include "Cintex/Cintex.h"
        
        int main()
        {
          ROOT::Cintex::Cintex::Enable();
          return 0;
        }
        ''',
        use="ROOT Cintex",
        execute   = True,
        mandatory = True,
        )

    ctx.env.HEPWAF_FOUND_ROOT = 1
    return

## EOF ##
