# -*- python -*-

# stdlib imports ---
import os
import os.path as osp

# waf imports ---
import waflib.Utils
import waflib.Logs as msg
import waflib.Configure
import waflib.Build
import waflib.Task
import waflib.Tools.ccroot
from waflib.Configure import conf
from waflib.TaskGen import feature, before_method, after_method, extension, after

#
_heptooldir = osp.dirname(osp.abspath(__file__))

def options(ctx):

    ctx.load('compiler_c compiler_cxx python')
    ctx.load('hep-waftools-base', tooldir=_heptooldir)

    ctx.add_option(
        '--with-root-sys',
        default=None,
        help="Look for CERN ROOT System at the given path")
    return

def configure(ctx):
    ctx.load('compiler_c compiler_cxx')
    ctx.load('hep-waftools-base', tooldir=_heptooldir)
    return

@conf
def find_cernroot(ctx, **kwargs):
    
    ctx.load('hep-waftools-base find_python', tooldir=_heptooldir)

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
    
    ctx.find_program(
        root_cfg, 
        var='ROOT-CONFIG',
        **kwargs)
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

    # check for gccxml
    if not ctx.env.HEPWAF_FOUND_GCCXML:
        ctx.find_gccxml()
        pass

    # -- check everything is kosher...
    version = ctx.check_cxx(
        msg="Checking ROOT version",
        okmsg="ok",
        fragment='''\
        #include "RVersion.h"
        #include <iostream>

        int main(int argc, char* argv[]) {
          std::cout << ROOT_RELEASE;
          return 0;
        }
        ''',
        use="ROOT",
        define_name = "HEPWAF_ROOT_VERSION",
        define_ret = True,
        execute  = True,
        mandatory=True,
        )
    ctx.start_msg("ROOT version")
    ctx.end_msg(version)

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

### ---
waflib.Tools.ccroot.USELIB_VARS['gen_reflex'] = set(['GCCXML_FLAGS', 'DEFINES', 'INCLUDES', 'CPPFLAGS', 'LIB'])

@feature('gen_reflex')
@after_method('apply_incpaths')
def gen_reflex_dummy(self):
    pass

@extension('.h')
def gen_reflex_hook(self, node):
    "Bind the .h file extension to the creation of a genreflex instance"
    source = node.name
    out_node_dir = self.path.get_bld().make_node(
        "_reflex_dicts").make_node(
        self.env['GENREFLEX_DICTNAME']
        )
    out_node_dir.mkdir()
    out_node = out_node_dir.make_node("%s.cxx" % source)
    dsomap_name = self.env['GENREFLEX_DSOMAP'].replace('--rootmap=','')
    dsomap_node = out_node_dir.make_node(dsomap_name)
    tsk = self.create_task('gen_reflex', node, [out_node,dsomap_node])
    #tsk = self.create_task('gen_reflex', node, out_node)
    self.source += tsk.outputs
    merge_dsomap_hook(self, dsomap_node).set_run_after(tsk)

# classes ---
class gen_reflex(waflib.Task.Task):
    vars = ['GENREFLEX', 'DEFINES', 'GCCXML_FLAGS', 'CPPFLAGS', 'INCLUDES']
    color= 'BLUE'
    run_str = '${GENREFLEX} ${SRC} -s ${GENREFLEX_SELECTION} -o ${TGT[0].abspath()} ${GCCXML_FLAGS} ${CPPPATH_ST:INCPATHS} ${DEFINES_ST:DEFINES} ${GENREFLEX_DSOMAP} ${GENREFLEX_DSOMAPLIB}'
    ext_in = ['.h',]
    ext_out= ['.cxx', '.dsomap']
    reentrant = True
    shell = False
    #shell = True

    def exec_command(self, cmd, **kw):
        cwd_node = self.outputs[0].parent
        out = self.outputs[0].change_ext('.genreflex.log')
        fout_node = cwd_node.find_or_declare(out.name)
        fout = open(fout_node.abspath(), 'w')
        kw['stdout'] = fout
        kw['stderr'] = fout
        rc = waflib.Task.Task.exec_command(self, cmd, **kw)
        if rc != 0:
            msg.error("** error running [%s]" % ' '.join(cmd))
            msg.error(fout_node.read())
        return rc
        
    def runnable_status(self):
        for tsk in self.run_after:
            if not getattr(tsk, 'hasrun', False):
                return waflib.Task.ASK_LATER
        for in_node in self.inputs:
            try:
                os.stat(in_node.abspath())
            except:
                return waflib.Task.ASK_LATER
        for out_node in self.outputs:
            try:
                os.stat(out_node.abspath())
            except:
                return waflib.Task.RUN_ME
        return waflib.Task.Task.runnable_status(self)

### ---------------------------------------------------------------------------
@feature('gen_map')
@after('symlink_tsk')
def schedule_gen_map(self):
    lnk_task = getattr(self, 'link_task', None)
    if not lnk_task:
        return
    for n in lnk_task.outputs:
        gen_map_hook(self, n)
    pass

@after('symlink_tsk')
def gen_map_hook(self, node):
    "Bind the .so file extension to the creation of a genmap task"
    dso = node.name
    bld_node = node.get_bld().parent
    dso_ext = self.dso_ext()
    out_node = bld_node.make_node(dso.replace(dso_ext,".dsomap"))
    tsk = self.create_task('gen_map', node, out_node)
    self.source += tsk.outputs
    merge_dsomap_hook(self, out_node).set_run_after(tsk)

class gen_map(waflib.Task.Task):
    vars = ['GENMAP', 'DEFINES', 'CPPFLAGS', 'INCLUDES']
    color= 'BLUE'
    run_str = '${GENMAP} -input-library ${SRC[0].name} -o ${TGT[0].name}'
    ext_in  = ['.so']
    ext_out = ['.dsomap']
    shell = False
    reentrant = True
    after = ['cxxshlib', 'cxxprogram', 'symlink_tsk']

    def exec_command(self, cmd, **kw):
        cwd_node = self.outputs[0].parent
        out = self.outputs[0].change_ext('.genmap.log')
        fout_node = cwd_node.find_or_declare(out.name)
        fout = open(fout_node.abspath(), 'w')
        kw['stdout'] = fout
        kw['stderr'] = fout
        kw['env'] = self._get_env_for_subproc()
        kw['cwd'] = self.inputs[0].get_bld().parent.abspath()
        rc = waflib.Task.Task.exec_command(self, cmd, **kw)
        if rc != 0:
            msg.error("** error running [%s]" % ' '.join(cmd))
            msg.error(fout_node.read())
        return rc

    def runnable_status(self):
        status = waflib.Task.Task.runnable_status(self)
        if status == waflib.Task.ASK_LATER:
            return status
        
        for out_node in self.outputs:
            try:
                os.stat(out_node.abspath())
            except:
                return waflib.Task.RUN_ME
        return status
    pass

### ---------------------------------------------------------------------------
def build_reflex_dict(self, name, source, selection_file, **kw):

    # extract package name
    PACKAGE_NAME = _get_pkg_name(self)

    source = waflib.Utils.to_list(source)[0]
    src_node = self.path.find_resource(source)
    if not src_node:
        # maybe in 'src' ?
        src_node = self.path.find_dir('src').find_resource(source)
        if src_node:
            source = os.path.join('src',source)
            
    kw = dict(kw)

    linkflags = [] # kw.get('linkflags', [])
    linkflags = self.env.SHLINKFLAGS + linkflags
    kw['linkflags'] = linkflags
    
    kw['includes'] = kw.get('includes',[])
    ## src_node = self.path.find_dir('src')
    ## if src_node:
    ##     kw['includes'].append(src_node.abspath())
    
    defines = kw.get('defines', [])
    _defines = []
    for d in self.env.CPPFLAGS:
        if d.startswith('-D'):
            _defines.append(d[len('-D'):])
        else:
            _defines.append(d)
    defines = _defines + defines
    kw['defines'] = defines + _get_pkg_version_defines(self) + ['__REFLEX__',]
    if self.is_dbg():
        #print(":"*80)
        # only add NDEBUG in dbg mode as it should already be added
        # by somebody else for -opt mode.
        kw['defines'].append('NDEBUG')
        pass
        
    #libs = kw.get('libs', [])
    #kw['libs'] = libs + ['Reflex']
    
    uses = kw.get('use', [])
    kw['use'] = uses + ['Reflex']

    def _maybe_tgen(*names):
        for name in names:
            try:
                return self.get_tgen_by_name(name), name
            except:
                pass
        return None, None
    dep_inc_dirs = []
    def _get_deps(obj):
        uses = getattr(obj, 'use', [])
        ld = obj.path.get_bld().abspath()
        dep_inc_dirs.extend(getattr(obj,'includes',[]))
        for u in uses:
            tgt,n = _maybe_tgen(u, 'complib-%s' % u, 'genreflex-%s' % u)
            if tgt:
                _get_deps(tgt)
    for u in kw['use']:
        tgt,n = _maybe_tgen(u)
        if tgt:
            _get_deps(tgt)
    kw['includes'] = dep_inc_dirs + kw['includes']
    target = kw['target'] = kw.get('target', name+'Dict')
    del kw['target']
    defines= kw['defines']
    del kw['defines']
    o = self.new_task_gen(
        features='gen_reflex cxx cxxshlib symlink_tsk',
        name='genreflex-%s' % name,
        source=source,
        target=target,
        reentrant=False,
        #libpath = self.env.LD_LIBRARY_PATH,
        libpath = self.env.LD_LIBRARY_PATH + [self.path.get_bld().abspath()],
        defines=defines,
        **kw
        )
    o.env.GENREFLEX = self.env['GENREFLEX']
    o.env.GCCXML_USER_FLAGS = ['-D__GNUC_MINOR__=2',]
    o.env.GCCXML_FLAGS = [
        #'--quiet',
        '--debug',
        '--gccxmlopt=--gccxml-cxxflags',
        '--fail_on_warnings',
        #'--gccxmlpath=',
        ]
    lib_name = "lib%s" % (o.target,) # FIXME !!
    o.env.GENREFLEX_DSOMAP = '--rootmap=%s.dsomap' % lib_name
    o.env.GENREFLEX_DSOMAPLIB = '--rootmap-lib=%s.so' % lib_name
    
    if self.is_32b():
        o.env.GCCXML_FLAGS.append('--gccxmlopt=-m32')
        o.env.GCCXML_FLAGS.append('--gccxmlopt=--gccxml-cxxflags -m32')
    else:
        o.env.GCCXML_FLAGS.append('--gccxmlopt=-m64')
        o.env.GCCXML_FLAGS.append('--gccxmlopt=--gccxml-cxxflags -m64')
        
    o.env.GENREFLEX_SELECTION = self.path.find_resource(selection_file).abspath()
    o.env.GENREFLEX_DICTNAME = name
    return o

### ------------------------------------------------------------------------
def build_rootcint_dict(self, name, source, target,
                      **kw):
    kw = dict(kw)

    _src = []
    for s in waflib.Utils.to_list(source):
        s = self.path.ant_glob(s)
        _src.extend(s)
    source = _src
    del _src
    
    includes = kw.get('includes', [])
    tgtdir = self.bldnode.find_or_declare(target).parent.abspath()
    kw['includes'] = [
        self.path.abspath(),
        self.bldnode.abspath(),
        tgtdir,
        ] + includes
    self.env.append_unique('INCPATHS', tgtdir)
    
    defines = kw.get('defines', [])
    defines.insert(0, 'R__ACCESS_IN_SYMBOL=1')
    kw['defines'] = defines
    
    env = self.env
    incpaths = [env.CPPPATH_ST % x for x in kw['includes']]
    o = self.new_task_gen(
        rule='${ROOTCINT} -f ${TGT} -c ${ROOTCINTINCPATHS} ${SRC}',
        name='rootcint-dict-%s' % name,
        source=source,
        target=target,
        reentrant=True,
        **kw
        )
    o.env['ROOTCINTINCPATHS'] = incpaths
    return o

waflib.Build.BuildContext.build_reflex_dict = build_reflex_dict
waflib.Build.BuildContext.build_rootcint_dict = build_rootcint_dict

## EOF ##
