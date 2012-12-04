# -*- python -*-

# stdlib imports
import os
import os.path as osp
import sys

# waf imports ---
import waflib.Configure
import waflib.ConfigSet
import waflib.Utils
import waflib.Logs as msg

_heptooldir = osp.dirname(osp.abspath(__file__))

g_HEPWAF_PROJECT_INFO = 'project.info'

def options(ctx):
    #msg.info("[options] hep-waftools-project-mgr...")
    #grp = ctx.add_option_group('hepwaf options')
    ctx.add_option(
        "--projects",
        action='store',
        default=None,
        help="colon-separated list of paths to projects this project depends on",
        )
    return

# def configure(ctx):
#     msg.info("[configure] hep-waftools-project-mgr...")
#     return

@waflib.Configure.conf
def _hepwaf_configure_project(ctx):
    '''
    _hepwaf_configure_project configures the current project.
    it setups the projects dependency tree and then configures each local
    package.

    needs: ctx.env.CMTPKGS
           ctx.env.INSTALL_AREA
    '''

    if not ctx.env.CMTPKGS:
        ctx.fatal('CMTPKGS needs to be defined')
        pass

    if not ctx.env.INSTALL_AREA:
        ctx.fatal('INSTALL_AREA needs to be defined')
        pass
        
    cmtpkgs = osp.abspath(ctx.env.CMTPKGS)
    install_area = ctx.env.INSTALL_AREA
    
    #ctx.msg("cmtpkgs", cmtpkgs)
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
    ctx.env.HEPWAF_PROJECT_ROOT = osp.abspath(os.getcwd())
    ctx.env.HEPWAF_PROJECT_INFOS = {
        'name': ctx.env.HEPWAF_PROJECT_NAME,
        'root': ctx.env.HEPWAF_PROJECT_ROOT,
        'deps': [],
        'pkgs': [],
        }
    ctx._hepwaf_configure_projects_tree()

    ## FIXME:
    ctx.env.PROJNAME = ctx.env.HEPWAF_PROJECT_NAME
    
    ## configure packages
    ctx._hepwaf_configure_packages()
    
    return

@waflib.Configure.conf
def _hepwaf_configure_projects_tree(ctx, projname=None, projpath=None):
    if projname is None: projname = ctx.hepwaf_project()
    if projpath is None: projpath = ctx.hepwaf_project_root()

    all_good = True
    #msg.info("projname: %s" % projname)
    #msg.info("projpath: %s" % projpath)
    ctx.hepwaf_add_project(projname)
    ctx.hepwaf_set_project_path(projname, projpath)

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
        proj_dir = ctx.root.find_dir(projpath)
        # try from destdir, before bailing out
        if not proj_dir and ctx.env.DESTDIR:
            pp = osp.abspath(projpath)
            pp = osp.abspath(ctx.env.DESTDIR) + pp
            proj_dir = ctx.root.find_dir(pp)
            pass
        if not proj_dir:
            msg.warn("could not locate project at [%s]" % projpath)
            continue
        try:
            proj_infos = proj_dir.ant_glob('**/%s' % g_HEPWAF_PROJECT_INFO)
        except:
            all_good = False
            continue
        if not proj_infos:
            msg.error("could not locate %s file at [%s]"
                      % (g_HEPWAF_PROJECT_INFO, proj_dir.abspath()))
            all_good = False
            continue
        
        if len(proj_infos) != 1:
            msg.error("invalid project infos at [%s] (got %s file(s))" %
                      (proj_dir.abspath(), len(proj_infos)))
            all_good = False
            continue
        proj_node = proj_infos[0]
        #print proj_node.abspath()
        
        denv = waflib.ConfigSet.ConfigSet()
        denv.load(proj_node.abspath())
        ppname = denv['HEPWAF_PROJECT_NAME']
        envvars = denv['HEPWAF_RUNTIME_ENVVARS']
        projdeps += [ppname]
        ctx.hepwaf_add_project(ppname)
        ctx.hepwaf_set_project_path(ppname, projpath)

        _proj_prefix = denv['PREFIX']
        if _proj_prefix == '@@HEPWAF_PREFIX@@':
            _proj_prefix = proj_dir.abspath()
            pass
        
        _proj_destdir= denv['DESTDIR']
        # automatically prepend DESTDIR if PREFIX does not exist...
        if _proj_destdir and not ctx.root.find_dir(_proj_prefix):
            _proj_prefix = osp.abspath(_proj_prefix)
            _proj_prefix = osp.abspath(_proj_destdir) + _proj_prefix
            pass

        def _un_massage(v):
            if isinstance(v, type("")):
                return v.replace('@@HEPWAF_PREFIX@@', _proj_prefix)
            elif isinstance(v, (list, tuple)):
                vv = []
                for ii in v:
                    vv.append(_un_massage(ii))
                    pass
                return type(v)(vv)
            elif isinstance(v, (int, float)):
                return v
            else:
                ctx.fatal('unhandled type %s' % type(v))
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
                env.prepend_value('INCPATHS', _un_massage(denv[k]))
                continue
            if k in ('INSTALL_AREA_LIBDIR', 'LIBPATH'):
                env.prepend_value('LIBPATH', _un_massage(denv[k]))
                continue
            if k in ('INSTALL_AREA_BINDIR', 'PATH'):
                env.prepend_value('PATH', _un_massage(denv[k]))
                continue

            if k in envvars:
                ctx.declare_runtime_env(k)
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
                     'CMTPKGS',
                     ):
                continue
            if k.startswith('HEPWAF_') or k.endswith('_PATTERN'):
                continue
            # print "-- import [%s] from [%s] %r" % (k, ppname, denv[k])
            v = _un_massage(denv[k])
            if isinstance(v, list):
                #env.prepend_unique(k, v)
                env.prepend_value(k, v)
            else:
                #ctx.fatal('invalid type (%s) for [%s]' % (type(v),k))
                env[k] = v
        pass # loop over proj-paths
    if not all_good:
        ctx.fatal("error(s) while configuring project dependency tree")
        pass
    # FIXME: windows(tm) handling !!
    if 'LIBPATH' in env.keys():
        env.prepend_value('LD_LIBRARY_PATH', env['LIBPATH'])
        if ctx.is_darwin():
            env.prepend_value('DYLD_LIBRARY_PATH', env['LIBPATH'])
        
    if ctx.is_darwin():
        # special handling of ['bar', '-arch', 'foo', 'baz']
        #-> regroup as ['bar', ('-arch','foo'), 'baz'] so the ctx.append_unique
        # will work correctly
        def _regroup(lst):
            if not '-arch' in lst:
                return lst
            v = []
            idx = 0
            while idx < len(lst):
                o = lst[idx]
                if o == '-arch':
                    o = (lst[idx], lst[idx+1])
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
            ctx.env.append_unique(k, _regroup(v))
            ctx.env[k] = _flatten(ctx.env[k])
        else:
            #ctx.fatal('invalid type (%s) for [%s]' % (type(v), k))
            #ctx.env wins...
            if not k in ctx.env.keys():
                ctx.env[k] = v
            pass
        pass
    #ctx.waffle_project_deps(projname)[:] = projdeps
    ctx.env['HEPWAF_PROJECT_DEPS_%s' % projname] = projdeps
    if ctx.env.PATH:
        ctx.env.PATH = os.pathsep.join(ctx.env.PATH)

    return

@waflib.Configure.conf
def _hepwaf_install_project_infos(ctx):
    node = ctx.bldnode.make_node(g_HEPWAF_PROJECT_INFO)
    env = ctx.env.copy()
    del env.HEPWAF_PROJECT_ROOT

    prefix = ctx.env.PREFIX
    def _massage(v):
        if isinstance(v, type("")):
            return v.replace(prefix, '@@HEPWAF_PREFIX@@')
        elif isinstance(v, (list, tuple)):
            vv = []
            for ii in v:
                vv.append(_massage(ii))
                pass
            return type(v)(vv)
        elif isinstance(v, (int, float)):
            return v
        elif isinstance(v ,(dict,)):
            vv = {}
            for kk in v.keys():
                vv[kk] = _massage(v[kk])
                pass
            return vv
        else:
            ctx.fatal('unhandled type %s' % type(v))
            pass
        return v
    
    # massage env to make it relocate-able...
    for k in env.keys():
        env[k] = _massage(env[k])
        pass

    env.store(node.abspath())
    node.sig = waflib.Utils.h_file(node.abspath())

    ctx.install_files('${INSTALL_AREA}', [node])

@waflib.Configure.conf
def _hepwaf_configure_packages(ctx):
    ctx._hepwaf_build_pkg_deps(pkgdir=ctx.env.CMTPKGS)
    return


### API for project queries
@waflib.Configure.conf
def hepwaf_project_names(self):
    return self.env['HEPWAF_PROJECT_NAMES']

@waflib.Configure.conf
def hepwaf_add_project(self, projname):
    self.env.append_unique('HEPWAF_PROJECT_NAMES', projname)

@waflib.Configure.conf
def hepwaf_project_infos(self):
    '''return the setup-dict for the current project'''
    return self.env['HEPWAF_PROJECT_INFOS']

@waflib.Configure.conf
def hepwaf_project(self):
    '''return the name of the current project'''
    return self.env['HEPWAF_PROJECT_NAME']

@waflib.Configure.conf
def hepwaf_project_root(self):
    '''return the root path of the current project'''
    return self.env['HEPWAF_PROJECT_ROOT']

@waflib.Configure.conf
def hepwaf_set_project_path(self, projname, projpath):
    if not projname in self.hepwaf_project_names():
        raise KeyError('no such project [%s] (values=%s)'%
                       (projname,self.hepwaf_project_names()))
    self.env['HEPWAF_PROJECT_PATH_%s' % projname] = projpath

@waflib.Configure.conf
def hepwaf_get_project_path(self, projname=None):
    if projname is None:
        projname = self.hepwaf_project()
        pass
    if not projname in self.hepwaf_project_names():
        raise KeyError('no such project [%s] (values=%s)'%
                       (projname,self.hepwaf_project_names()))
    return self.env['HEPWAF_PROJECT_PATH_%s'%projname]
    
@waflib.Configure.conf
def hepwaf_project_deps(self, projname=None):
    '''return the list of projects projname depends on'''
    if projname is None:
        projname = self.hepwaf_project()
        pass
    if not projname in self.hepwaf_project_names():
        raise KeyError('no such project [%s] (values=%s)'%
                       (projname,self.hepwaf_project_names()))
    return self.env['HEPWAF_PROJECT_DEPS_%s'%projname]

### API for package queries
@waflib.Configure.conf
def hepwaf_pkg_deps(self, pkgname, projname=None):
    return self.env['HEPWAF_PKGDEPS_%s'%pkgname]

@waflib.Configure.conf
def hepwaf_pkgs(self, projname=None):
    '''return the list of package full-names for the current project'''
    return self.env['HEPWAF_PKGNAMES']

@waflib.Configure.conf
def hepwaf_add_pkg(self, pkgname, projname=None):
    self.env.append_unique('HEPWAF_PKGNAMES', pkgname)
    return

@waflib.Configure.conf
def hepwaf_has_pkg(self, pkgname, projname=None):
    return pkgname in self.hepwaf_pkgs(projname)

@waflib.Configure.conf
def hepwaf_pkg_dirs(self, projname=None):
    '''return the path to the packages from the current project'''
    return self.env['HEPWAF_PKGDIRS']

### ---------------------------------------------------------------------------
@waflib.Configure.conf
def _hepwaf_build_pkg_deps(ctx, pkgdir=None):
    """process all packages and build the dependency graph"""

    if pkgdir is None: pkgdir = ctx.env.CTMPKGS
    ctx.pkgdir = pkgdir = ctx.path.find_dir(pkgdir)
    if not pkgdir:
        ctx.msg("pkg-dir", "<N/A>")
        return
    #ctx.msg("pkg-dir", pkgdir.abspath())

    pkgs = ctx.hepwaf_find_subpackages(pkgdir.name)
    #ctx.msg("local packages", str(len(pkgs)))
    for pkg in pkgs:
        #msg.info(" %s" % pkg.path_from(pkgdir))
        pkgname = pkg.path_from(pkgdir)
        ctx.hepwaf_add_pkg(pkgname)
        ctx.env['HEPWAF_PKGDEPS_%s' % pkgname] = []

    ctx.recurse([pkg.abspath() for pkg in pkgs], name='pkg_deps')

    pkglist = []
    def process_pkg(pkg, parent=None):
        deps = ctx.hepwaf_pkg_deps(pkg)
        for ppkg in deps:
            if ppkg in pkglist:
                continue
            process_pkg(ppkg, pkg)
        if not (pkg in pkglist):
            if not ctx.hepwaf_has_pkg(pkg):
                ctx.fatal('package [%s] depends on *UNKNOWN* package [%s]' %
                          (parent, pkg,))
            pkglist.append(pkg)
    for pkg in ctx.hepwaf_pkgs():
        process_pkg(pkg)
        pass
    
    ctx.env['HEPWAF_PKGNAMES'] = pkglist[:]
    ctx.env['HEPWAF_PKGDIRS'] = []
    topdir = os.path.dirname(waflib.Context.g_module.root_path)
    topdir = ctx.root.find_dir(topdir)
    for pkgname in pkglist:
        #print "--",pkgname,pkgdir.abspath()
        pkg = ctx.pkgdir.find_node(pkgname)
        pkgname = pkg.path_from(topdir)
        ctx.env.append_unique('HEPWAF_PKGDIRS', pkgname)
    return

### ---------------------------------------------------------------------------
class PkgList(waflib.Configure.ConfigurationContext):
    '''gives the list of packages in the current project'''

    cmd = 'pkglist'
    #fun = 'build'

    def execute(self):
        ctx = self
        cmtpkgs = ctx.env.CMTPKGS
        pkgdir = ctx.path.find_dir(cmtpkgs)
        assert pkgdir, "no such directory: [%s]" % cmtpkgs
        msg.info("pkg-dir: %s" % pkgdir.abspath())
        pkgs = ctx.hepwaf_find_subpackages(pkgdir.name)
        for pkg in pkgs:
            msg.info(" %s" % pkg.path_from(pkgdir))
            pass

        self.pkgs = pkgs
        self.pkgdir = pkgdir
        return
    pass # PkgList
waflib.Context.g_module.__dict__['_hepwaf_pkg_list'] = PkgList

### ---------------------------------------------------------------------------
class PkgMgr(waflib.Configure.ConfigurationContext):
    '''finds and creates the list of packages in the current project'''

    cmd = 'pkgmgr'

    
    def execute(self):
        return self._hepwaf_build_pkg_deps()

    pass # PkgMgr
waflib.Context.g_module.__dict__['_hepwaf_pkgmgr'] = PkgMgr

@waflib.Configure.conf
def use_pkg(ctx,
            pkgname, version=None,
            public=None, private=None,
            runtime=None):
    pkg = ctx.path.path_from(ctx.root.find_dir(ctx.pkgdir.abspath()))
    ## print "--------"
    ## print "ctx:",ctx
    ## print "pkg:",pkg
    ## print "dep:",pkgname
    ## print "path:",ctx.path.abspath()
    ctx.env.append_unique('HEPWAF_PKGNAMES', pkg)
    ctx.env.append_unique('HEPWAF_PKGDEPS_%s' % pkg, pkgname)
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
        pkgnames = self.hepwaf_pkgs()
        if not self.hepwaf_has_pkg(pkgname):
            self.fatal('package [%s] not in package list:\npkgs: %s' %
                       (pkgname,pkgnames))
        pkgdeps = self.hepwaf_pkg_deps(pkgname)
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
waflib.Context.g_module.__dict__['_hepwaf_show_pkg_uses'] = ShowPkgUses

### ---------------------------------------------------------------------------
import waflib.Build
class ShowProjects(waflib.Build.BuildContext):
    '''shows the tree of projects for the current project'''

    cmd = 'show-projects'

    def execute_build(self):
        self.show_projects(projname=self.hepwaf_project())
        return

    def get_project_uses(self, projname):
        projnames = self.env['HEPWAF_PROJECT_NAMES']
        if not projname in projnames:
            self.fatal('project [%s] not in project list:\nprojects: %s' %
                       (projname, projnames))
            pass
        projdeps = self.env['HEPWAF_PROJECT_DEPS_%s' % projname]
        return projdeps

    def do_display_project_uses(self, projname, depth=0):
        projdeps = self.get_project_uses(projname)
        msg.info('%s%s' % ('  '*depth, projname))
        for projdep in projdeps:
            self.do_display_project_uses(projdep, depth+1)
            pass
        return
    
    def show_projects(self, projname):
        projdeps = self.get_project_uses(projname)
        msg.info('project dependency list for [%s] (#projs=%s)' %
                 (projname, len(projdeps)))
        self.do_display_project_uses(projname)
        return
    
    pass # ShowProjects
waflib.Context.g_module.__dict__['_hepwaf_show_projects'] = ShowProjects

## EOF ##
