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

    ctx.load('hwaf-base', tooldir=_heptooldir)
    ctx.load('find_libxml2',      tooldir=_heptooldir)
    ctx.load('find_python',       tooldir=_heptooldir)
    ctx.load('find_gccxml', tooldir=_heptooldir)

    ctx.add_option(
        '--with-root',
        default=None,
        help="Look for CERN ROOT System at the given path")
    return

def configure(ctx):
    ctx.load('hwaf-base', tooldir=_heptooldir)
    return

@conf
def find_root(ctx, **kwargs):
    
    ctx.load('hwaf-base', tooldir=_heptooldir)
    ctx.load('find_python', tooldir=_heptooldir)
    ctx.load('find_libxml2', tooldir=_heptooldir)
    ctx.load('find_gccxml', tooldir=_heptooldir)

    if not ctx.env.HWAF_FOUND_C_COMPILER:
        ctx.fatal('load a C compiler first')
        pass

    if not ctx.env.HWAF_FOUND_CXX_COMPILER:
        ctx.fatal('load a C++ compiler first')
        pass

    if not ctx.env.HWAF_FOUND_PYTHON:
        ctx.find_python(version=kwargs.get('python_version', (2,6)))
    
    if not ctx.env.HWAF_FOUND_LIBXML2:
        ctx.find_libxml2(mandatory=False)
    
    if not ctx.env.PYTHON:
        ctx.fatal('load a python interpreter first')
        pass

    # find root
    root_cfg = "root-config"
    path_list = waflib.Utils.to_list(kwargs.get('path_list', []))
    for topdir in [getattr(ctx.options, 'with_root', None), os.getenv('ROOTSYS', None)]:
        if topdir:
            topdir = ctx.hwaf_subst_vars(topdir)
            path_list.append(
                osp.join(topdir, "bin")
                )
            pass
        pass
    kwargs['path_list']=path_list

    
    ctx.find_program(
        root_cfg, 
        var='ROOT-CONFIG',
        **kwargs)
    root_cfg = ctx.env['ROOT-CONFIG']

    ctx.check_with(
        ctx.check_cfg,
        "root",
        path=root_cfg,
        package="",
        uselib_store="ROOT",
        args='--libs --cflags --ldflags',
        **kwargs)

    ctx.find_program('genmap',      var='GENMAP',     **kwargs)
    ctx.find_program('genreflex',   var='GENREFLEX',  **kwargs)
    ctx.find_program('root',        var='ROOT-EXE',   **kwargs)
    ctx.find_program('rootcint',    var='ROOTCINT',   **kwargs)
    ctx.find_program('rlibmap',     var='RLIBMAP',     **kwargs)

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
    ctx.copy_uselib_defs(dst='ROOT-XMLIO', src='ROOT')
    ctx.env['LIB_ROOT-XMLIO'] = ['XMLIO']

    # XMLParser
    ctx.copy_uselib_defs(dst='ROOT-XMLParser', src='ROOT')
    ctx.env['LIB_ROOT-XMLParser'] = ['XMLParser']

    # TreePlayer
    ctx.copy_uselib_defs(dst='ROOT-TreePlayer', src='ROOT')
    ctx.env['LIB_ROOT-TreePlayer'] = ['TreePlayer']

    # check for gccxml
    if not ctx.env.HWAF_FOUND_GCCXML:
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
        define_name = "HWAF_ROOT_VERSION",
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
        mandatory= True,
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
        msg="Checking for pyroot-cxx",
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

    # check for ROOTSYS env. variable.
    ctx.start_msg('Checking for $ROOTSYS')
    rootsys = ctx.env.ROOTSYS
    if not rootsys:
        rootsys = os.getenv('ROOTSYS', None)
        pass
    if not rootsys:
        # make up one.
        rootsys = ctx.env.ROOT_HOME
        pass
    if not rootsys:
        # make up one.
        rootsys = getattr(ctx.options, 'with_root', None)
        pass
    ctx.end_msg(rootsys)
    if not rootsys:
        ctx.fatal("No $ROOTSYS environment variable")
        pass
    ctx.env.ROOTSYS = ctx.hwaf_subst_vars(rootsys)
    ctx.hwaf_declare_runtime_env('ROOTSYS')

    ctx.env.prepend_value('PATH', osp.join(ctx.env.ROOTSYS, 'bin'))
    ctx.env.prepend_value('LD_LIBRARY_PATH', osp.join(ctx.env.ROOTSYS, 'lib'))
    
    pyroot_path = osp.join(ctx.env.ROOTSYS, 'lib')
    ctx.env.prepend_value('PYTHONPATH', pyroot_path)
    ctx.env.prepend_value('LD_LIBRARY_PATH', pyroot_path)

    # check also python environment
    ctx.find_python_module('ROOT')
    ctx.find_python_module('PyCintex')

    ctx.env.ROOT_VERSION = version

    # register the find_root module
    import sys
    fname = __file__
    if fname.endswith('.pyc'): fname = fname[:-1]
    ctx.hwaf_export_module(ctx.root.find_node(fname).abspath())

    ctx.env.HWAF_FOUND_ROOT = 1
    return

### ---------------------------------------------------------------------------
g_dsomap_merger = None
@feature('merge_dsomap')
def schedule_merge_dsomap(self):
    #bld_area = self.env['BUILD_INSTALL_AREA']
    pass

@extension('.dsomap')
def merge_dsomap_hook(self, node):
    global g_dsomap_merger
    if g_dsomap_merger is None:
        import os
        bld_area = os.path.basename(self.env['BUILD_INSTALL_AREA'])
        bld_node = self.bld.bldnode.find_dir(bld_area)
        if not bld_node:
            bld_node = self.bld.bldnode.make_node(bld_area)
            
        out_node = bld_node.make_node('lib').make_node(
            'project_%s_merged.rootmap' %
            self.bld.hwaf_project_name().replace('-', '_')
            )
        g_dsomap_merger = self.create_task('merge_dsomap', node, out_node)
        self.bld.install_files(
            '${INSTALL_AREA}/lib',
            out_node,
            relative_trick=False
            )
    else:
        g_dsomap_merger.inputs.append(node)
    return g_dsomap_merger

class merge_dsomap(waflib.Task.Task):
    color='PINK'
    ext_in = ['.dsomap']
    ext_out= ['.rootmap']
    after = ['gen_map', 'gen_reflex', 'symlink_tsk']
    run_str = 'cat ${SRC} > ${TGT}'
    shell = True

    def runnable_status(self):
        status = waflib.Task.Task.runnable_status(self)
        if status == waflib.Task.ASK_LATER:
            return status
        
        import os
        for in_node in self.inputs:
            try:
                os.stat(in_node.abspath())
            except:
                msg.debug("::missing input [%s]" % in_node.abspath())
                return waflib.Task.ASK_LATER
        return waflib.Task.RUN_ME
    
### ---------------------------------------------------------------------------
waflib.Tools.ccroot.USELIB_VARS['gen_reflex'] = set(['GCCXML_FLAGS', 'DEFINES', 'INCLUDES', 'CPPFLAGS', 'LIB'])

@feature('gen_reflex')
@after_method('apply_incpaths')
def gen_reflex_dummy(self):
    pass

#@extension('.h')
def gen_reflex_hook(self, node):
    "Bind the .h file extension to the creation of a genreflex instance"
    if not self.env['GENREFLEX_DSOMAP']:
        # project with *no* Reflex target...
        return
    if not self.env['GENREFLEX']:
        # project configuration failed to find genreflex binary
        self.bld.fatal(
            'package [%s] requested a gen_reflex task but binary "genreflex" not found (re-check configuration options)' %
            self.bld.hwaf_pkg_name(self.path)
        )
        return
    if not self.env['HWAF_FOUND_GCCXML']:
        # project configuration failed to find genreflex binary
        self.bld.fatal(
            'package [%s] requested a gen_reflex task but binary "gccxml" not found (re-check configuration options)' %
            self.bld.hwaf_pkg_name(self.path)
        )
        return

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
    vars = ['GENREFLEX', 'GENREFLEX_SELECTION', 'DEFINES', 'GCCXML_FLAGS', 'CPPFLAGS', 'INCLUDES']
    color= 'BLUE'
    run_str = '${GENREFLEX} ${SRC} -s ${GENREFLEX_SELECTION} -o ${TGT[0].abspath()} ${GCCXML_FLAGS} ${CPPPATH_ST:INCPATHS} ${DEFINES_ST:DEFINES} ${GENREFLEX_DSOMAP} ${GENREFLEX_DSOMAPLIB}'
    ext_in = ['.h']
    ext_out= ['.cxx', '.dsomap']
    reentrant = True
    shell = False
    #shell = True

    def scan(self):
        selfile = self.env['GENREFLEX_SELECTION']
        node = self.generator.bld.root.find_resource(selfile)
        return ([node], waflib.Utils.h_file(node.abspath()))

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
    dso_ext = self.bld.dso_ext()
    out_node = bld_node.make_node(dso.replace(dso_ext,".dsomap"))
    tsk = self.create_task('gen_map', node, out_node)
    self.source += tsk.outputs
    merge_dsomap_hook(self, out_node).set_run_after(tsk)

class gen_map(waflib.Task.Task):
    vars = ['GENMAP', 'DEFINES', 'CPPFLAGS', 'INCLUDES']
    color= 'BLUE'
    run_str = '${GENMAP} -input-library ${SRC[0].name} -o ${TGT[0].name}'
    ext_in  = ['.so', '.dylib', '.dll', '.bin']
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
        kw['env'] = self.generator.bld._get_env_for_subproc()
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
    PACKAGE_NAME = self._get_pkg_name()

    source = self._cmt_get_srcs_lst(source)
    src_node = source[0]
            
    kw = dict(kw)

    kw['name'] = name

    linkflags = [] # kw.get('linkflags', [])
    linkflags = self.env.SHLINKFLAGS + linkflags
    kw['linkflags'] = linkflags
    
    kw['includes'] = waflib.Utils.to_list(kw.get('includes',[]))
    bld_node = self.root.find_dir(self.env['BUILD_INSTALL_AREA'])
    if not bld_node:
        bld_node = self.root.make_node(self.env['BUILD_INSTALL_AREA'])
    kw['includes'].append(bld_node.parent.abspath())

    defines = waflib.Utils.to_list(kw.get('defines', []))
    kw['defines'] = defines + self._get_pkg_version_defines() + ['__REFLEX__',]
    if self.is_dbg():
        #print(":"*80)
        # only add NDEBUG in dbg mode as it should already be added
        # by somebody else for -opt mode.
        kw['defines'].append('NDEBUG')
        pass
        
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
        uses = waflib.Utils.to_list(getattr(obj, 'use', []))
        ld = obj.path.get_bld().abspath()
        includes = waflib.Utils.to_list(getattr(obj,'includes',[]))
        for inc in includes:
            if isinstance(inc, type("")):
                inc_node = obj.path.find_dir(inc)
            else:
                inc_node = inc
            if inc_node:
                dep_inc_dirs.append(inc_node.abspath())
        for u in uses:
            tgt,n = _maybe_tgen(u, 'complib-%s' % u, 'genreflex-%s' % u)
            if tgt:
                _get_deps(tgt)
    for u in kw['use']:
        tgt,n = _maybe_tgen(u)
        if tgt:
            _get_deps(tgt)
    kw['includes'] = dep_inc_dirs + kw['includes']

    kw['target'] =target = kw.get('target', name+'Dict')
    del kw['target']

    features = waflib.Utils.to_list(kw.get('features', [])) + [
        'gen_reflex', 'cxx', 'cxxshlib', 'symlink_tsk',
        ]
    kw['features'] = features

    defines= kw['defines']
    del kw['defines']

    o = self(
        source=source,
        target=target,
        defines=defines,
        **kw
        )

    o.name = 'genreflex-%s' % name
    o.libpath = self.env.LD_LIBRARY_PATH + [self.path.get_bld().abspath()]
    o.install_path ='${INSTALL_AREA}/lib'
    o.reentrant = False
    o.depends_on = [self.path.find_resource(selection_file)]
    o.mappings['.h'] = gen_reflex_hook
    
    o.env.GENREFLEX = self.env['GENREFLEX']
    o.env.GCCXML_USER_FLAGS = ['-D__GNUC_MINOR__=2',]
    o.env.GCCXML_FLAGS = [
        #'--quiet',
        '--debug',
        '--gccxmlopt=--gccxml-cxxflags', '--fail_on_warnings',
        #'--gccxmlopt=--gccxml-cxxflags', '-D__STRICT_ANSI__',
        self.hwaf_subst_vars('--gccxmlpath=${GCCXML_BINDIR}', o.env),
        #'--gccxmlpath=',
        ]
    if 'clang' in o.env.CFG_COMPILER:
        if self.is_darwin():
            # latest macosx XCode-5 needs to use llvm-gcc as a compiler b/c of
            # system headers gcc can't grok
            o.env.append_unique('GCCXML_FLAGS', '--gccxmlopt=--gccxml-compiler llvm-gcc')
        else:
            # FIXME: for the moment, always using gcc is fine
            #        even in the context of a clang-based toolchain.
            #        This should be revisited w/ VisualStudio...
            o.env.append_unique('GCCXML_FLAGS', '--gccxmlopt=--gccxml-compiler gcc')
        pass
      
    lib_name = "lib%s" % (o.target,) # FIXME !!
    o.env.GENREFLEX_DSOMAP = '--rootmap=%s.dsomap' % lib_name
    o.env.GENREFLEX_DSOMAPLIB = '--rootmap-lib=%s.so' % lib_name
    
    if self.is_32b():
        o.env.GCCXML_FLAGS.append('--gccxmlopt=-m32')
        #o.env.GCCXML_FLAGS.append('--gccxmlopt=--gccxml-cxxflags -m32')
    else:
        o.env.GCCXML_FLAGS.append('--gccxmlopt=-m64')
        #o.env.GCCXML_FLAGS.append('--gccxmlopt=--gccxml-cxxflags -m64')
        pass
    
    o.env.GENREFLEX_SELECTION = self.path.find_resource(selection_file).abspath()
    o.env.GENREFLEX_DICTNAME = name
    return o

### ---------------------------------------------------------------------------
waflib.Tools.ccroot.USELIB_VARS['gen_rootcint'] = set(['DEFINES', 'INCLUDES', 'CPPFLAGS', 'LIB'])

@feature('gen_rootcint')
@after_method('apply_incpaths')
def gen_rootcint_dummy(self):
    pass

#@extension('.h')
def gen_rootcint_hook(self, node):
    "Bind the .h file extension to the creation of a gen_rootcint instance"
    if not self.env['GENROOTCINT_DICTNAME']:
        # project with *no* rootcint target...
        return
    source = node.name
    out_node_dir = self.path.get_bld().make_node(
        "_rootcint_dicts").make_node(
        self.env['GENROOTCINT_DICTNAME']
        )

    bld_node = out_node_dir
    out_node = bld_node.make_node(source.replace(".h",".cxx"))
    tsk = self.create_task('gen_rootcint', node, [out_node,])
    self.source += tsk.outputs
    #merge_dsomap_hook(self, dsomap_node).set_run_after(tsk)

class gen_rootcint(waflib.Task.Task):
    vars = ['ROOTCINT', 'ROOTCINT_LINKDEF', 'DEFINES', 'CPPFLAGS', 'INCLUDES']
    color= 'BLUE'
    run_str = '${ROOTCINT} -f ${TGT} -c ${ROOTCINTINCPATHS} ${CPPPATH_ST:INCPATHS} ${DEFINES_ST:DEFINES} ${SRC} ${ROOTCINT_LINKDEF}'
    ext_in = ['.h']
    ext_out= ['.cxx']
    reentrant = True
    shell = False
    #shell = True
    #after = ['apply_incpaths',]
    
    def scan_(self):
        linkdef = self.env['ROOTCINT_LINKDEF']
        linkdef_node = self.generator.bld.root.find_resource(linkdef)
        src_node = self.inputs[0]
        o=waflib.Utils.h_file(src_node.abspath())
        return ([linkdef_node,src_node],
                [waflib.Utils.h_file(linkdef_node.abspath()), o])

    def exec_command(self, cmd, **kw):
        cwd_node = self.outputs[0].parent
        out = self.outputs[0].change_ext('.genrootcint.log')
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
@feature('gen_rootcint_map')
@after('symlink_tsk')
def schedule_gen_rootcint_map(self):
    lnk_task = getattr(self, 'link_task', None)
    if not lnk_task:
        return
    for n in lnk_task.outputs:
        gen_rootcint_map_hook(self, n)
    pass

@extension('.bin')
def gen_rootcint_map_hook(self, node):
    "Create a rootmap file for a rootcint dict"
    dso = node.name
    bld_node = node.get_bld().parent
    dso_ext = self.bld.dso_ext()
    out_node = bld_node.make_node(dso.replace(dso_ext,".dsomap"))
    tsk = self.create_task('gen_rootcint_map', node, out_node)
    self.source += tsk.outputs
    merge_dsomap_hook(self, out_node).set_run_after(tsk)

class gen_rootcint_map(waflib.Task.Task):
    vars = ['RLIBMAP', 'DEFINES', 'CPPFLAGS', 'INCLUDES', 'RLIBMAP_LINKDEF']
    color= 'BLUE'
    #run_str = '${GENMAP} -input-library ${SRC[0].name} -o ${TGT[0].name}'
    run_str = '${RLIBMAP} -o ${TGT[0].name} -l ${SRC} -c ${RLIBMAP_LINKDEF}'
    ext_in  = ['.so', '.dylib', '.dll', '.bin']
    ext_out = ['.dsomap']
    shell = False
    reentrant = True
    after = ['cxxshlib', 'cxxprogram', 'symlink_tsk']

    def exec_command(self, cmd, **kw):
        cwd_node = self.outputs[0].parent
        out = self.outputs[0].change_ext('.gen_rootcint_map.log')
        fout_node = cwd_node.find_or_declare(out.name)
        fout = open(fout_node.abspath(), 'w')
        kw['stdout'] = fout
        kw['stderr'] = fout
        kw['env'] = self.generator.bld._get_env_for_subproc()
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

### ------------------------------------------------------------------------
def build_rootcint_dict(self, name, source, **kw):
    kw = dict(kw)

    # extract package name
    PACKAGE_NAME = self._get_pkg_name()

    srcs = self._cmt_get_srcs_lst(source)

    includes = waflib.Utils.to_list(kw.get('includes', []))
    tgtdir = self.bldnode.find_or_declare(name).parent.abspath()
    kw['includes'] = [
        self.path.abspath(),
        self.bldnode.abspath(),
        tgtdir,
        ] + includes
    
    defines = waflib.Utils.to_list(kw.get('defines', []))
    defines.insert(0, 'R__ACCESS_IN_SYMBOL=1')
    kw['defines'] = defines

    kw['rootcint_linkdef'] = kw.get('rootcint_linkdef', 'src/LinkDef.h')
    linkdef_node = self.path.find_node(kw['rootcint_linkdef'])

    kw['features'] = waflib.Utils.to_list(kw.get('features', [])) + [
        'gen_rootcint', 'gen_rootcint_map', 'cxx', 'symlink_tsk',
        ]

    env = self.env
    incpaths = [env.CPPPATH_ST % x for x in kw['includes']]
    o = self(
        name = name,
        source=source,
        **kw
        )
    o.mappings['.h'] = gen_rootcint_hook
    if not 'cxxshlib' in o.features:
        o.name = 'rootcint-dict-%s' % name
    o.reentrant = True
    o.depends_on = [linkdef_node.abspath()]
    o.env['ROOTCINT_LINKDEF'] = linkdef_node.abspath()
    o.env['RLIBMAP_LINKDEF'] = linkdef_node.abspath()
    o.env['GENROOTCINT_DICTNAME'] = name
    return o

waflib.Build.BuildContext.build_reflex_dict = build_reflex_dict
waflib.Build.BuildContext.build_rootcint_dict = build_rootcint_dict

## EOF ##
