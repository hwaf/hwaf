# -*- python -*-

# stdlib imports
import os
import os.path as osp
import sys

# waf imports ---
import waflib.Configure
import waflib.ConfigSet
import waflib.Node
import waflib.Utils
import waflib.Logs as msg

_heptooldir = osp.dirname(osp.abspath(__file__))

g_HWAF_PROJECT_INFO = 'project.info'
g_HWAF_MODULE_FMT = '__hwaf_module__%s'

def options(ctx):
    #msg.info("hwaf: [options] hwaf-project-mgr...")
    #grp = ctx.add_option_group('hepwaf options')
    ctx.add_option(
        "--projects",
        action='store',
        default=None,
        help="colon-separated list of paths to projects this project depends on",
        )
    return

def configure(ctx):
    # msg.info("hwaf: [configure] hwaf-project-mgr...")
    return

def build(ctx):
    return

@waflib.Configure.conf
def _hwaf_configure_project(ctx):
    '''
    _hwaf_configure_project configures the current project.
    it setups the projects dependency tree and then configures each local
    package.

    needs: ctx.env.PKGDIR
           ctx.env.INSTALL_AREA
    '''

    if not ctx.env.PKGDIR:
        ctx.fatal('PKGDIR needs to be defined')
        pass

    if not ctx.env.INSTALL_AREA:
        ctx.fatal('INSTALL_AREA needs to be defined')
        pass
        
    pkgdir = osp.abspath(ctx.env.PKGDIR)
    install_area = ctx.env.INSTALL_AREA
    
    #ctx.msg("pkg dir", pkgdir)
    #ctx.msg("install-area", install_area)
    
    ctx.env.INSTALL_AREA_INCDIR = os.path.join(install_area,'include')
    ctx.env.INSTALL_AREA_BINDIR = os.path.join(install_area,'bin')
    ctx.env.INSTALL_AREA_LIBDIR = os.path.join(install_area,'lib')

    binstall_area = ctx.bldnode.make_node('.install_area').abspath()
    ctx.env.BUILD_INSTALL_AREA = binstall_area
    ctx.env.BUILD_INSTALL_AREA_INCDIR = os.path.join(binstall_area,'include')
    ctx.env.BUILD_INSTALL_AREA_BINDIR = os.path.join(binstall_area,'bin')
    ctx.env.BUILD_INSTALL_AREA_LIBDIR = os.path.join(binstall_area,'lib')

    #ctx.msg("bld-install", binstall_area)

    ## init project tree structure
    ctx.env.HWAF_PROJECT_ROOT = osp.abspath(os.getcwd())
    ctx.env.HWAF_PROJECTS = {
        ctx.env.HWAF_PROJECT_NAME : {
            'name': ctx.env.HWAF_PROJECT_NAME,
            'root': ctx.env.HWAF_PROJECT_ROOT,
            'deps': [],
            'pkgs': {},
            'dirs': [],
            },
        }
    ctx._hwaf_configure_projects_tree()

    ## configure packages
    ctx._hwaf_configure_packages()
    
    # create the project hwaf module...
    hwaf=ctx._hwaf_create_project_hwaf_module()
    return

@waflib.Configure.conf
def _hwaf_configure_projects_tree(ctx, projname=None, projpath=None):
    if projname is None: projname = ctx.hwaf_project_name()
    if projpath is None: projpath = ctx.hwaf_project_root()

    all_good = True
    #msg.info("hwaf: projname: %s" % projname)
    #msg.info("hwaf: projpath: %s" % projpath)
    ctx.hwaf_set_project_path(projname, projpath)

    projdeps = ctx.options.projects
    if not projdeps: projdeps = []
    elif isinstance(projdeps, type("")): projdeps = projdeps.split(":")
    else:
        ctx.fatal("invalid --projects option (type=%s value=%s)"
                  % (type(projdeps), projdeps))
        pass

    projpaths = projdeps[:]
    projdeps = []
    
    env = waflib.ConfigSet.ConfigSet()
    for projpath in projpaths:
        if not projpath:
            continue
        #msg.info("hwaf: >>>>>>>>> %s" % projpath)
        projpath = osp.expanduser(osp.expandvars(projpath))
        projpath = osp.abspath(projpath)
        proj_dir = ctx.root.find_dir(projpath)
        # try from destdir, before bailing out
        if not proj_dir and ctx.env.DESTDIR:
            pp = osp.abspath(projpath)
            pp = osp.abspath(ctx.env.DESTDIR) + pp
            proj_dir = ctx.root.find_dir(pp)
            pass
        if not proj_dir:
            msg.warn("hwaf: could not locate project at [%s]" % projpath)
            continue
        try:
            proj_infos = proj_dir.ant_glob('**/%s' % g_HWAF_PROJECT_INFO)
        except:
            all_good = False
            msg.warn("hwaf: could not locate project at [%s]" % projpath)
            continue

        if not proj_infos:
            msg.error("hwaf: could not locate %s file at [%s]"
                      % (g_HWAF_PROJECT_INFO, proj_dir.abspath()))
            all_good = False
            continue
        
        if len(proj_infos) != 1:
            msg.error("hwaf: invalid project infos at [%s] (got %s file(s))" %
                      (proj_dir.abspath(), len(proj_infos)))
            all_good = False
            continue
        proj_node = proj_infos[0]
        #print proj_node.abspath()
        
        denv = waflib.ConfigSet.ConfigSet()
        denv.load(proj_node.abspath())
        proj_dicts = dict(denv['HWAF_PROJECTS'])
        ppname = denv['HWAF_PROJECT_NAME']
        proj_dict = proj_dicts[ppname]
        envvars = denv['HWAF_RUNTIME_ENVVARS'][:]
        projdeps += [ppname]
        ctx.hwaf_import_projects(proj_dicts)
        ctx.hwaf_set_project_path(ppname, projpath)
        ctx.hwaf_project_deps(projname).append(ppname)

        # add packages from this project...
        for pkg in proj_dict['pkgs'].keys():
            # msg.info("hwaf: @@@ pkg=%s deps=%s"
            #           % (pkg, proj_dict['pkgs'][pkg]['deps']))
            ctx.hwaf_add_pkg(
                pkg,
                projname=ppname,
                deps=proj_dict['pkgs'][pkg]['deps'],
                pkgdir=proj_dict['pkgs'][pkg]['dir'],
                )
            pass
        
        _proj_topdir = denv['HWAF_RELOCATE']
        _proj_prefix = denv['HWAF_PREFIX']
        if _proj_prefix.startswith('@@HWAF_RELOCATE@@'):
            _relocate_topdir = _proj_topdir.replace("@@HWAF_RELOCATE@@", "")
            _relocate_prefix = _proj_prefix.replace("@@HWAF_RELOCATE@@", "")
            _proj_prefix = proj_dir.abspath()
            if _relocate_topdir == "": _relocate_topdir = '/'
            if _relocate_prefix == "": _relocate_prefix = '/'
            # msg.info("hwaf: _relocate_topdir: %s" % _relocate_topdir)
            # msg.info("hwaf: _relocate_prefix: %s" % _relocate_prefix)
            # msg.info("hwaf: _delta:           %s" % osp.relpath(_relocate_topdir, _relocate_prefix))
            _proj_topdir = osp.realpath(
                osp.join(_proj_prefix,
                         osp.relpath(_relocate_topdir, _relocate_prefix))
                )
            pass
        
        _proj_destdir= denv['DESTDIR']
        # automatically prepend DESTDIR if PREFIX does not exist...
        if _proj_destdir and not ctx.root.find_dir(_proj_prefix):
            # msg.info("="*80)
            # msg.info("hwaf: :: massaging following destdir...")
            # msg.info("hwaf: :: destdir: [%s]" % _proj_destdir)
            # msg.info("hwaf: :: -prefix: [%s]" % _proj_prefix)
            pp = osp.abspath(_proj_destdir) + osp.abspath(_proj_prefix)
            pp = ctx.root.find_dir(pp)
            if not pp:
                msg.error("hwaf: could not locate project at [%s]" % _proj_prefix)
                all_good = False
                continue
            # msg.info("hwaf: :: +prefix: [%s]" % pp)
            _proj_prefix = pp
            pass

        # msg.info("="*80)
        # msg.info("hwaf: project: %s" % ppname)
        # msg.info("hwaf: topdir:  %s" % _proj_topdir)
        # msg.info("hwaf: prefix:  %s" % _proj_prefix)
        # msg.info("hwaf: destdir: %s" % _proj_destdir)
        # msg.info("hwaf: pypath:  %s" % denv['PYTHONPATH'])
        
        def _un_massage(k, v):
            if isinstance(v, type("")):
                return v.replace('@@HWAF_RELOCATE@@', _proj_topdir)
            elif isinstance(v, (list, tuple)):
                vv = []
                for ii in v:
                    vv.append(_un_massage(k,ii))
                    pass
                return type(v)(vv)
            elif isinstance(v, (int, float)):
                return v
            elif isinstance(v ,(dict,)):
                vv = {}
                for kk in v.keys():
                    vv[kk] = _un_massage(kk, v[kk])
                    pass
                return vv
            else:
                ctx.fatal('unhandled type %s (key=%r, value=%r)' % (type(v),k, v))
                pass
            return v

        # import uses from this project into our own
        from waflib.Tools.ccroot import USELIB_VARS
        vv = set([])
        for kk in USELIB_VARS.keys():
            vv |= USELIB_VARS[kk]
        vv = tuple([ii+"_" for ii in vv])
        for k in denv.keys():
            if k in ('INSTALL_AREA_INCDIR', 'INCPATHS'):
                env.prepend_value('INCPATHS', _un_massage(k,denv[k]))
                continue
            if k in ('INSTALL_AREA_LIBDIR', 'LIBPATH'):
                env.prepend_value('LIBPATH', _un_massage(k,denv[k]))
                continue
            if k in ('INSTALL_AREA_BINDIR', 'PATH'):
                env.prepend_value('PATH', _un_massage(k,denv[k]))
                continue

            if k in envvars:
                ctx.hwaf_declare_runtime_env(k)
                pass
            
            if k in ('ARCH_ST', 'DEFINES_ST',
                     'FRAMEWORKPATH_ST', 'FRAMEWORK_ST',
                     'LIBPATH_ST', 'LIB_ST',
                     'RPATH_ST', 
                     'STLIBPATH_ST', 'STLIB_ST',
                     'BUILD_INSTALL_AREA',
                     'PREFIX',
                     'LIBDIR',
                     'BINDIR',
                     'VERSION',
                     'PKGDIR',
                     ):
                continue
            # if k.startswith('HWAF_') or k.endswith('_PATTERN'):
            #     continue
            # if k.endswith('_PATTERN'):
            #     continue
            if k.startswith('HWAF_') and \
                   not k.startswith(('HWAF_FOUND_',
                                     'HWAF_TAGS',
                                     'HWAF_ACTIVE_TAGS')):
                continue
            # print "-- import [%s] from [%s] %r" % (k, ppname, denv[k])
            v = _un_massage(k,denv[k])
            if isinstance(v, list):
                #env.prepend_unique(k, v)
                env.prepend_value(k, v)
            else:
                #ctx.fatal('invalid type (%s) for [%s]' % (type(v),k))
                env[k] = v
            pass

        # import hwaf modules from this project, if any
        hwaf_mod_dir = osp.join(_un_massage('INSTALL_AREA',denv["INSTALL_AREA"]),
                                "share", "hwaf")
        hwaf_mod_name = g_HWAF_MODULE_FMT % (ppname.replace("-","_"),)
        hwaf_fname = osp.join(hwaf_mod_dir, hwaf_mod_name+".py")
        ctx._hwaf_load_project_hwaf_module(hwaf_fname, do_export=True)
        pass # loop over proj-paths
    
    if not all_good:
        ctx.fatal("error(s) while configuring project dependency tree")
        pass
    # FIXME: windows(tm) handling !!
    if 'LIBPATH' in env.keys():
        env.prepend_value('LD_LIBRARY_PATH', env['LIBPATH'])
        if ctx.is_darwin():
            env.prepend_value('DYLD_LIBRARY_PATH', env['LIBPATH'])
        
    if ctx.is_darwin() or ctx.is_linux():
        # special handling of ['bar', '-arch', 'foo', 'baz']
        #-> regroup as ['bar', ('-arch','foo'), 'baz'] so the ctx.append_unique
        # will work correctly
        def _regroup(lst):
            if not '-arch' in lst and not '-include' in lst:
                return lst
            v = []
            idx = 0
            while idx < len(lst):
                o = lst[idx]
                if o in ('-arch', '-include'):
                    o = [lst[idx], lst[idx+1]]
                    idx += 1
                    pass
                v.append(o)
                idx += 1
            return v
        def _flatten(lst):
            o = []
            for i in lst:
                if isinstance(i, (list,tuple)): o.extend(i)
                else:                           o.append(i)
            return o
    else:
        def _regroup(v): return v
        def _flatten(v): return v
        pass

    
    # merge all
    for k in env.keys():
        v = env[k]
        if isinstance(v, list):
            ctx.env[k] = _regroup(ctx.env[k])
            for vv in _regroup(v):
                if not vv in ctx.env[k]:
                    ctx.env.prepend_value(k, vv)
            ctx.env[k] = _flatten(ctx.env[k])
        else:
            #ctx.fatal('invalid type (%s) for [%s]' % (type(v), k))
            #ctx.env wins...
            if not k in ctx.env.keys():
                ctx.env[k] = v
            pass
        pass
    #ctx.hwaf_project_deps(projname).extend(projdeps)
    #ctx.env['HWAF_PROJECT_DEPS_%s' % projname] = projdeps
    if ctx.env.PATH:
        #ctx.env.PATH = os.pathsep.join(ctx.env.PATH)
        pass

    # bootstrap the toolchain
    ctx.load('find_compiler')
    if ctx.env.HWAF_FOUND_TOOLCHAIN:
        # reimport
        kw_c_args = {}
        if ctx.env.HWAF_FOUND_C_COMPILER:
            cc = os.environ['CC'] = ctx.env.get_flat('CC')
            kw_c_args = dict(override=True, path_list=[osp.dirname(cc)])
            pass
        ctx.find_c_compiler(**kw_c_args)

        kw_cxx_args = {}
        if ctx.env.HWAF_FOUND_CXX_COMPILER:
            cxx = os.environ['CXX'] = ctx.env.get_flat('CXX')
            kw_cxx_args = dict(path_list=[osp.dirname(cxx)], override=True)
            pass
        ctx.find_cxx_compiler(**kw_cxx_args)

        kw_fc_args = {"mandatory": False}
        if ctx.env.HWAF_FOUND_FC_COMPILER:
            fc = os.environ['FC'] = ctx.env.get_flat('FC')
            kw_fc_args = dict(path_list=[osp.dirname(fc)], 
                              mandatory=True,
                              override=True)
            pass
        ctx.find_fortran_compiler(**kw_fc_args)
        pass
    else:
        ctx.find_toolchain()
    
    msg.debug("hwaf: INCPATHS: %s" % ctx.env['INCPATHS'])
    msg.debug("hwaf: PYTHONPATH: %s" % ctx.env['PYTHONPATH'])
    ctx.env.prepend_value('INCLUDES', ctx.env.INCPATHS)
    
    return

### ---------------------------------------------------------------------------
import waflib.TaskGen
@waflib.TaskGen.feature('*')
@waflib.TaskGen.after_method(
    'apply_vnum','apply_link', 'apply_bundle',
    'propagate_uselib_vars', 'propagate_use',
    )
def hwaf_schedule_project_infos(self):
    fct = getattr(self, '_hwaf_install_project_infos', None)
    if not fct: fct = getattr(self.bld, '_hwaf_install_project_infos')
    #fct()
    return

@waflib.Configure.conf
def _hwaf_install_project_infos(ctx):

    msg.debug('hwaf: _hwaf_install_project_infos(%s)...' % ctx.cmd)
    if ctx.cmd in ('clean',):
        return

    node = ctx.bldnode.make_node(g_HWAF_PROJECT_INFO)
    ctx.hwaf_setup_runtime()
    env = ctx.env.derive()
    # msg.info(":"*80)
    # msg.info(env['PYTHONPATH'])
    env.detach()
    del env.HWAF_PROJECT_ROOT
    del env.HWAF_MODULES
    env['HWAF_PREFIX'] = env.PREFIX

    destdir = None
    if ctx.env.DESTDIR: destdir = ctx.env.DESTDIR

    pkgdir = ctx.env.PKGDIR
    pkgdir = ctx.path.find_node(pkgdir)
    if not pkgdir: ctx.fatal("could not find pkgdir node [%s]" % pkgdir)
    src_pkgdir = pkgdir.get_src().abspath()
    bld_pkgdir = pkgdir.get_bld().abspath()
    
    relocate = ctx.env.HWAF_RELOCATE
    def _massage(k,v):
        if isinstance(v, type("")):
            # prevent hysteresis: remove $DESTDIR we might have added
            if destdir and v.startswith(destdir) and 1:
                msg.debug("hwaf: destdir: %s" % destdir)
                msg.debug("hwaf: v: %s" % v)
                v = v[len(destdir):]
                pass
            # remove local paths
            if v.startswith((src_pkgdir, bld_pkgdir)):
                msg.debug("hwaf: discarding [%s]" % v)
                return None
            # only replace when it *starts* with relocate
            # to prevent hysteresis effects.
            if v.startswith(relocate):
                v = v.replace(relocate, '@@HWAF_RELOCATE@@')
            return v
        elif isinstance(v, (list, tuple)):
            vv = []
            for ii in v:
                ii = _massage(k, ii)
                if ii: vv.append(ii)
                pass
            return type(v)(vv)
        elif isinstance(v, (int, float)):
            return v
        elif isinstance(v ,(dict,)):
            vv = {}
            for kk in v.keys():
                vv[kk] = _massage(kk, v[kk])
                pass
            return vv
        elif v is None:
            return v
        else:
            ctx.fatal('unhandled type %s (key=%r, value=%r)' % (type(v), k, v))
            pass
        return v
    
    # massage env to make it relocate-able...
    for k in env.keys():
        env[k] = _massage(k, env[k])
        pass

    env.store(node.abspath())
    node.sig = waflib.Utils.h_file(node.abspath())

    ctx.install_files(
        '${INSTALL_AREA}',
        [node],
        postpone=False,
        )

    hwaf = ctx._hwaf_create_project_hwaf_module()
    hwaf.sig = waflib.Utils.h_file(hwaf.abspath())
    ctx.install_files(
        '${INSTALL_AREA}/share/hwaf', [hwaf],
        postpone=False,
        )
    msg.debug('hwaf: _hwaf_install_project_infos(%s)... [done]' % ctx.cmd)
    return

@waflib.Configure.conf
def _hwaf_get_project_hwaf_module(ctx, fname=None):
    if fname is None:
        fname = g_HWAF_MODULE_FMT % ctx.env.HWAF_PROJECT_NAME.replace(
            "-",
            "_"
            )
        fname += ".py"
        pass
    if osp.isabs(fname): hwaf = ctx.root.find_node(fname)
    else:
        hwaf = ctx.bldnode.find_node(fname)
        if not hwaf: hwaf = ctx.path.find_node(fname)
        pass
    if not hwaf:
        msg.info("hwaf: could not find hwaf-module [%s]" % (fname,))
        return None
    return hwaf

@waflib.Configure.conf
def _hwaf_create_project_hwaf_module(ctx):
    # create a hwaf-module/<project-name>
    hwaf_fname = g_HWAF_MODULE_FMT % ctx.env.HWAF_PROJECT_NAME.replace(
        "-",
        "_"
        )
    hwaf = ctx.bldnode.make_node(hwaf_fname+".py")
    hwaf.write("# -*- python -*-\n"+
               "## modules from [%s]\n" % ctx.env.HWAF_PROJECT_NAME,
               flags="w")
    for mod in ctx.env.HWAF_MODULES:
        mnode = ctx.root.find_node(mod)
        if not mnode:ctx.fatal("could not find hwaf-module [%s]" % mod)
        msg.debug("hwaf: create_project_hwaf_module: %s" % mod)
        hwaf.write("\n", flags="a")
        hwaf.write("#"*80, flags="a")
        mod_name = mnode.srcpath()
        hwaf.write("\n### beg: %s\n" % mod_name, flags="a")
        hwaf.write(mnode.read(), flags="a")
        hwaf.write("\n### end: %s\n" % mod_name, flags="a")
        hwaf.write("#"*80, flags="a")
        pass
    hwaf.write("\n", flags="a")
    hwaf.write("## EOF ##\n", flags="a")
    return hwaf

@waflib.Configure.conf
def _hwaf_load_project_hwaf_module(ctx, fname=None, do_export=False):
    hwaf = ctx._hwaf_get_project_hwaf_module(fname)
    if not hwaf: return hwaf
    hwaf_fname = hwaf.abspath()
    hwaf_mod_name = osp.basename(hwaf_fname)
    if hwaf_mod_name.endswith(".py"):
        hwaf_mod_name = hwaf_mod_name[:-len(".py")]
    hwaf_mod_dir = osp.dirname(hwaf_fname)
    if not osp.exists(hwaf_fname):
        ctx.fatal("no such hwaf-module file [%s]" % hwaf_fname)
        pass
    waflib.Context.Context.load(
        ctx,
        hwaf_mod_name,
        tooldir=hwaf_mod_dir,
        name="__hwaf_module_load__",
        )
    if do_export:
        # register that file to export so each project is self-contained
        ctx.hwaf_export_module(hwaf_fname)
    return hwaf

@waflib.Configure.conf
def _hwaf_configure_packages(ctx):
    ctx._hwaf_build_pkg_deps(pkgdir=ctx.env.PKGDIR)
    return


### API for project queries
@waflib.Configure.conf
def hwaf_project_names(self):
    return list(self.hwaf_projects().keys())

@waflib.Configure.conf
def hwaf_add_project(self, projdict):
    if not isinstance(projdict, dict):
        raise TypeError(
            "hwaf_add_project takes a dict as argument (got %r)"
            % type(projdict)
            )
    projname = projdict['name']
    if projname in self.env['HWAF_PROJECTS'].keys():
        msg.warn(
            'hwaf: project with name [%s] already in project-db ! (ignoring the re-import)' %
            projname)
        return
    self.env['HWAF_PROJECTS'][projname] = projdict

@waflib.Configure.conf
def hwaf_import_projects(self, projdicts):
    for projname,projdict in projdicts.items():
        self.hwaf_add_project(projdict)
        pass
    return

@waflib.Configure.conf
def hwaf_projects(self):
    '''return the full project info tree'''
    return self.env['HWAF_PROJECTS']

@waflib.Configure.conf
def hwaf_project(self):
    '''return the setup-dict for the current project'''
    return self._hwaf_get_project(self.env['HWAF_PROJECT_NAME'])

@waflib.Configure.conf
def hwaf_project_name(self):
    '''return the name of the current project'''
    return self.hwaf_project()['name']

@waflib.Configure.conf
def hwaf_project_root(self):
    '''return the root path of the current project'''
    return self.hwaf_project()['root']

@waflib.Configure.conf
def _hwaf_get_project(self, projname=None):
    if projname is None:
        projname = self.hwaf_project_name()
        pass
    try:
        return self.hwaf_projects()[projname]
    except:
        raise KeyError(
            'no such project [%s] (values=%s)'%
            (projname,self.hwaf_project_names())
            )
    
@waflib.Configure.conf
def hwaf_set_project_path(self, projname, projpath):
    self._hwaf_get_project(projname)['root'] = projpath
    return

@waflib.Configure.conf
def hwaf_get_project_path(self, projname=None):
    return self._hwaf_get_project(projname)['root']
    
@waflib.Configure.conf
def hwaf_project_deps(self, projname=None):
    '''return the list of projects projname depends on'''
    return self._hwaf_get_project(projname)['deps']

@waflib.Configure.conf
def hwaf_itr_projects(self, projname=None):
    '''return an iterator over projects, following project deps'''
    def _itr_proj(projname):
        p = self._hwaf_get_project(projname)
        yield p
        for pp in p['deps']:
            for ppp in _itr_proj(pp):
                yield ppp
                pass
            pass
        return
    for proj in _itr_proj(projname):
        #msg.info("::itr:: %s..." % proj['name'])
        yield proj
        pass
    return

# @waflib.Configure.conf
# def hwaf_find_project_for_pkg(self, pkgname, projname=None):
#     '''finds the first package ``pkgname`` honoring project-deps'''
#     for proj in self.hwaf_itr_projects(projname):
#         msg.info("??? proj [%s]..." % proj['name'])
#         pkgs = proj['pkgs']
#         try:
#             _ = pkgs[pkgname]
#             return proj
#         except KeyError:
#             pass
#     raise KeyError('no such package [%s] in any of the projects\n%s' %
#                    (pkgname, self.hwaf_projects()))

### API for package queries
@waflib.Configure.conf
def hwaf_pkg_infos(self, pkgdir=None):
    if pkgdir is None: pkgdir = self.path
    if isinstance(pkgdir, waflib.Node.Node): pkgdir = pkgdir.abspath()
    mod = waflib.Context.load_module(osp.join(pkgdir, waflib.Context.WSCRIPT_FILE))
    try:
        package = getattr(mod, 'PACKAGE')
    except AttributeError:
        raise waflib.Errors.WafError('package [%s] has not "PACKAGE" attribute' % pkgdir)
    return package

@waflib.Configure.conf
def hwaf_pkg_name(self, pkgdir=None):
    return self.hwaf_pkg_infos(pkgdir)['name']

@waflib.Configure.conf
def hwaf_pkg_deps(self, pkgname, projname=None):
    #msg.info(">>> deps[%s]..." % (pkgname,))
    pkg = self.hwaf_find_pkg(pkgname, projname)
    deps = pkg['deps']
    #msg.info("+++ deps[%s]: %s" % (pkgname, deps))
    return deps

@waflib.Configure.conf
def hwaf_pkgs(self, projname=None):
    '''return the list of package full-names for the current project'''
    proj = self._hwaf_get_project(projname)
    pkgs = list(proj['pkgs'].keys())
    #msg.info("** pkgs: %s" % pkgs)
    return pkgs

@waflib.Configure.conf
def hwaf_add_pkg(self, pkgname, projname=None, deps=None, pkgdir=None):
    if deps is None:
        deps = []
    if pkgdir is None:
        pkgdir = osp.dirname(pkgname)
    proj = self._hwaf_get_project(projname)
    msg.debug("hwaf: add-pkg(%s, %s)..." % (pkgname, proj['name']))
    proj['pkgs'][pkgname] = {
        'deps': deps,
        'name': osp.basename(pkgname),
        'full_name': pkgname,
        'dir': pkgdir,
        }
    return

@waflib.Configure.conf
def hwaf_has_pkg(self, pkgname, projname=None):
    try:
        self.hwaf_find_pkg(pkgname, projname)
        return True
    except KeyError:
        return False
    return False

@waflib.Configure.conf
def hwaf_find_pkg(self, pkgname, projname=None):
    '''finds the first package ``pkgname`` honoring project-deps'''
    #msg.info("*"*80)
    msg.debug("hwaf: --> looking for pkg[%s]..." % pkgname)
    for proj in self.hwaf_itr_projects(projname):
        #msg.info("??? proj [%s]..." % proj['name'])
        pkgs = proj['pkgs']
        try:
            pkg = pkgs[pkgname]
            #msg.info("??? proj [%s]... YEAAAAAAH!" % proj['name'])
            return pkg
        except KeyError:
            pass
    from pprint import pformat
    errmsg = "hwaf: no such package [%s] in any of the projects\n%s" % \
             (pkgname, pformat(self.hwaf_projects()))
    msg.error(errmsg)
    raise KeyError("hwaf: no such package [%s]" % pkgname)

@waflib.Configure.conf
def hwaf_pkg_dirs(self, projname=None):
    '''return the path to the packages from the current project'''
    proj = self._hwaf_get_project(projname)
    return proj['dirs']

### ---------------------------------------------------------------------------
@waflib.Configure.conf
def _hwaf_build_pkg_deps(ctx, pkgdir=None):
    """process all packages and build the dependency graph"""

    if pkgdir is None: pkgdir = ctx.env.PKGDIR
    ctx.pkgdir = pkgdir = ctx.path.find_dir(pkgdir)
    if not pkgdir:
        ctx.msg("pkg-dir", "<N/A>")
        return
    #ctx.msg("pkg-dir", pkgdir.abspath())

    pkgs = ctx.hwaf_find_subpackages(pkgdir.path_from(ctx.path))
    #ctx.msg("local packages", str(len(pkgs)))
    for pkg in pkgs:
        #msg.info(" %s" % pkg.path_from(ctx.path))
        pkgpath = pkg.path_from(ctx.path)
        pkgname = ctx.hwaf_pkg_name(pkgpath)
        #msg.info(" => %s" % pkgname)
        ctx.hwaf_add_pkg(pkgname, pkgdir=pkgpath)
        pass
    
    ctx.recurse([pkg.abspath() for pkg in pkgs], name='pkg_deps')

    pkglist = []
    pkgstack = []
    def process_pkg(pkg, parent=None):
        pkgstack.append(pkg)
        deps = ctx.hwaf_pkg_deps(pkg)
        for ppkg in deps:
            if ppkg in pkglist:
                continue
            if ppkg in pkgstack:
                ctx.fatal('cycle detected: %s uses %s -> %s' % (pkg, ppkg, pkgstack))
                
            try:
                process_pkg(ppkg, pkg)
            except KeyError:
                ctx.fatal('package [%s] depends on *UNKNOWN* package [%s]' %
                          (pkg, ppkg,))
        if not (pkg in pkglist):
            if not ctx.hwaf_has_pkg(pkg):
                ctx.fatal('package [%s] depends on *UNKNOWN* package [%s]' %
                          (parent, pkg,))
            pkglist.append(pkg)

    for pkg in ctx.hwaf_pkgs():
        #msg.info("--> %s" % pkg)
        process_pkg(pkg)
        pkgstack = []
        pass
    
    topdir = os.path.dirname(waflib.Context.g_module.root_path)
    topdir = ctx.root.find_dir(topdir)
    for pkgname in pkglist:
        #msg.info("-- %s %s" % (pkgname, pkgdir.abspath()))
        pkgdict = ctx.hwaf_find_pkg(pkgname, projname=None)
        pkg = ctx.path.find_dir(pkgdict['dir'])
        if not pkg: # not a local package...
            continue
        #pkgname = pkg.path_from(topdir)
        ctx.hwaf_pkg_dirs().append(pkgdict['dir'])
    return

### ---------------------------------------------------------------------------
class PkgList(waflib.Configure.ConfigurationContext):
    '''gives the list of packages in the current project'''

    cmd = 'pkglist'
    #fun = 'build'

    def execute(self):
        ctx = self
        pkgdir = ctx.path.find_dir(ctx.env.PKGDIR)
        assert pkgdir, "no such directory: [%s]" % ctx.env.PKGDIR
        msg.debug("hwaf: pkg-dir: %s" % pkgdir.abspath())
        pkgs = ctx.hwaf_find_subpackages(pkgdir.path_from(ctx.path))
        for pkg in pkgs:
            msg.info(" %s" % pkg.path_from(pkgdir))
            pass

        self.pkgs = pkgs
        self.pkgdir = pkgdir
        return
    pass # PkgList
waflib.Context.g_module.__dict__['_hwaf_pkg_list'] = PkgList

### ---------------------------------------------------------------------------
class PkgMgr(waflib.Configure.ConfigurationContext):
    '''finds and creates the list of packages in the current project'''

    cmd = 'pkgmgr'

    
    def execute(self):
        return self._hwaf_build_pkg_deps()

    pass # PkgMgr
waflib.Context.g_module.__dict__['_hwaf_pkgmgr'] = PkgMgr

@waflib.Configure.conf
def use_pkg(ctx,
            pkgname, version=None,
            public=None, private=None,
            runtime=None):
    pkg = ctx.hwaf_pkg_name(ctx.path.abspath())
    # msg.info("========")
    # msg.info("ctx: %s" % ctx)
    # msg.info("pkg: %s" % pkg)
    # msg.info("dep: %s" % pkgname)
    # msg.info("path:%s" % ctx.path.abspath())
    ctx.hwaf_pkg_deps(pkg).append(pkgname)
    return


### ---------------------------------------------------------------------------
import waflib.Build
class ShowPkgUses(waflib.Build.BuildContext):
    '''shows the list of packages a given package depends on'''

    cmd = 'show-pkg-uses'

    def execute_build(self):
        if not waflib.Options.commands:
            self.fatal('%s expects at least one package name. got: %s' %
                       (self.cmd, waflib.Options.commands))
            
        while waflib.Options.commands:
            pkgname = waflib.Options.commands.pop(0)
            #print "pkgname:",pkgname
            self.show_pkg_uses(pkgname)
        return

    def get_pkg_uses(self, pkgname):
        pkgnames = self.hwaf_pkgs()
        if not self.hwaf_has_pkg(pkgname):
            self.fatal('package [%s] not in package list:\npkgs: %s' %
                       (pkgname,pkgnames))
        pkgdeps = self.hwaf_pkg_deps(pkgname)
        return sorted(pkgdeps)

    def do_display_pkg_uses(self, pkgname, depth=0, maxdepth=2):
        pkgdeps = self.get_pkg_uses(pkgname)
        msg.info('%s%s' % ('  '*depth, pkgname))
        depth += 1
        if depth < maxdepth:
            for pkgdep in pkgdeps:
                self.do_display_pkg_uses(pkgdep, depth)
            
    def show_pkg_uses(self, pkgname):
        pkgdeps = self.get_pkg_uses(pkgname)
        msg.info('package dependency list for [%s] (#pkgs=%s)' %
                 (pkgname, len(pkgdeps)))
        self.do_display_pkg_uses(pkgname)
        return
    pass # ShowPkgUses
waflib.Context.g_module.__dict__['_hwaf_show_pkg_uses'] = ShowPkgUses

### ---------------------------------------------------------------------------
import waflib.Build
class ShowPkgTree(waflib.Build.BuildContext):
    '''shows the dependency tree of packages for a given project'''

    cmd = 'show-pkg-tree'

    def execute_build(self):
        cmds = waflib.Options.commands[:]
        if not cmds:
            cmds = [self.hwaf_project_name()]
            
        while cmds:
            projname = cmds.pop(0)
            self.show_pkg_tree(projname)
        return

    def get_pkg_uses(self, pkgname):
        pkgnames = self.hwaf_pkgs()
        if not self.hwaf_has_pkg(pkgname):
            self.fatal('package [%s] not in package list:\npkgs: %s' %
                       (pkgname,pkgnames))
        pkgdeps = self.hwaf_pkg_deps(pkgname)
        return sorted(pkgdeps)

    def do_display_pkg_uses(self, pkgname, depth=0, maxdepth=2):
        pkgdeps = self.get_pkg_uses(pkgname)
        msg.info('%s%s' % ('  '*depth, pkgname))
        depth += 1
        if depth < maxdepth:
            for pkgdep in pkgdeps:
                self.do_display_pkg_uses(pkgdep, depth)
            
    def show_pkg_tree(self, projname):
        self.pkgdir = pkgdir = self.path.find_dir(self.env.PKGDIR)
        pkglist = self.hwaf_pkgs(projname)
        msg.info('package dependency tree for [%s] (#pkgs=%s)' %
                 (projname, len(pkglist)))
        for pkg in pkglist:
            self.do_display_pkg_uses(pkg)
        return
    pass # ShowPkgTree
waflib.Context.g_module.__dict__['_hwaf_show_pkg_tree'] = ShowPkgTree

### ---------------------------------------------------------------------------
import waflib.Build
class ShowProjects(waflib.Build.BuildContext):
    '''shows the tree of projects for the current project'''

    cmd = 'show-projects'

    def execute_build(self):
        self.show_projects(projname=self.hwaf_project_name())
        return

    def get_project_uses(self, projname):
        projnames = self.hwaf_project_names()
        if not projname in projnames:
            self.fatal('project [%s] not in project list:\nprojects: %s' %
                       (projname, projnames))
            pass
        projdeps = self.hwaf_project_deps(projname)
        return projdeps

    def do_display_project_uses(self, projname, depth=0):
        projdeps = self.get_project_uses(projname)
        msg.info('%s%s' % ('  '*depth, projname))
        for projdep in projdeps:
            self.do_display_project_uses(projdep, depth+1)
            pass
        return
    
    def show_projects(self, projname=None):
        if projname is None:
            projname = self.hwaf_project_name()
            pass
        projdeps = self.get_project_uses(projname)
        msg.info('project dependency list for [%s] (#projs=%s)' %
                 (projname, len(projdeps)))
        self.do_display_project_uses(projname)
        return
    
    pass # ShowProjects
waflib.Context.g_module.__dict__['_hwaf_show_projects'] = ShowProjects

## EOF ##
