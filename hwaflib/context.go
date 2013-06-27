package hwaflib

import (
	"bytes"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"runtime"
	"strings"

	gocfg "github.com/gonuts/config"
	"github.com/hwaf/hwaf/platform"
)

var (
	ErrNoHwafRootDir = errors.New("hwaf: no HWAF_ROOT directory")
)

func path_exists(name string) bool {
	_, err := os.Stat(name)
	if err == nil {
		return true
	}
	if os.IsNotExist(err) {
		return false
	}
	return false
}

// Context holds the necessary context informations for a hwaf installation
type Context struct {
	Root     string        // top-level directory of the hwaf installation
	sitedir  string        // top-level directory for s/w installation
	cmtcfg   string        // current CmtCfg
	workarea *string       // work directory for a local checkout
	gcfg     *gocfg.Config // the global configuration (user>global)
	lcfg     *gocfg.Config // the local config of a local workarea
	PkgDb    *PackageDb    // a naive database of locally checked out packages
}

func NewContext() (*Context, error) {
	var err error
	var ctx *Context

	ctx = &Context{
		Root:     "",
		sitedir:  "",
		cmtcfg:   "",
		workarea: nil,
		gcfg:     nil,
		lcfg:     nil,
		PkgDb:    nil,
	}

	err = ctx.init()
	return ctx, err
}

func NewContextFrom(workarea string) (*Context, error) {
	var err error
	var ctx *Context

	if !path_exists(workarea) {
		err = fmt.Errorf("hwaf: no such directory [%s]", workarea)
		return nil, err
	}

	wdir := string(workarea)
	ctx = &Context{
		Root:     "",
		sitedir:  "",
		cmtcfg:   "",
		workarea: &wdir,
		gcfg:     nil,
		lcfg:     nil,
		PkgDb:    nil,
	}

	err = ctx.init()
	return ctx, err
}

func (ctx *Context) WafBin() (string, error) {
	var err error

	wrkarea, err := ctx.Workarea()
	if err != nil {
		return "", fmt.Errorf("hwaf.WafBin: no workarea (err=%v). try running 'hwaf init .'", err)
	}

	top := filepath.Join(wrkarea, ".hwaf")
	waf := filepath.Join(top, "bin", "waf")
	if path_exists(waf) {
		return waf, nil
	}

	top = ctx.Root
	waf = filepath.Join(top, "bin", "waf")
	if path_exists(waf) {
		return waf, nil
	}

	// try from user .config
	top = os.ExpandEnv(filepath.Join("${HOME}", ".config", "hwaf"))
	waf = filepath.Join(top, "bin", "waf")
	if !path_exists(waf) {
		err = fmt.Errorf(
			"no such file [%s]\nplease re-run 'hwaf self init'\n",
			waf,
		)
		return "", err
	}

	return "", fmt.Errorf("could not find 'waf' binary")
}

func (ctx *Context) Sitedir() string {
	return ctx.sitedir
}

func (ctx *Context) Cmtcfg() string {
	return ctx.cmtcfg
}

func (ctx *Context) Workarea() (string, error) {
	if ctx.workarea != nil {
		return *ctx.workarea, nil
	}

	// FIXME: handle case where we are invoked from a submodule directory
	git := exec.Command(
		"git", "rev-parse", "--show-toplevel",
	)
	bout, err := git.Output()
	if err != nil {
		return "", err
	}
	out := strings.Trim(string(bout), " \r\n")
	out, err = filepath.Abs(out)
	if err == nil {
		ctx.workarea = &out
	}
	return *ctx.workarea, err
}

func (ctx *Context) DefaultCmtcfg() string {
	hwaf_os := runtime.GOOS
	hwaf_arch := runtime.GOARCH
	hwaf_comp := "gcc"
	switch hwaf_arch {
	case "amd64":
		hwaf_arch = "x86_64"
	case "386":
		hwaf_arch = "i686"
	default:
		//hwaf_arch = "unknown"
		panic(fmt.Sprintf("unknown architecture [%s]", hwaf_arch))
	}
	//FIXME: is 'gcc' a good enough default ?
	cmtcfg := fmt.Sprintf("%s-%s-%s-opt", hwaf_arch, hwaf_os, hwaf_comp)

	pinfos, err := platform.Infos()
	if err != nil {
		//println("*** error:" + err.Error())
		return cmtcfg
	}

	// try harder...
	cmtcfg2, err := ctx.infer_cmtcfg(pinfos, hwaf_arch, hwaf_os, hwaf_comp)
	if err != nil {
		//println("*** error:" + err.Error())
		return cmtcfg
	}
	cmtcfg = cmtcfg2
	return cmtcfg
}

func infer_gcc_version() (string, error) {
	re_gcc_vers := regexp.MustCompile(`.*? \(.*?\) ([\d.]+).*?`)
	out, err := exec.Command("gcc", "--version").Output()
	if err != nil {
		return "", err
	}

	lines := bytes.Split(out, []byte("\r\n"))
	line := string(lines[0])

	m := re_gcc_vers.FindStringSubmatch(line)
	if m == nil {
		return "", fmt.Errorf("hwaf: could not infer gcc version")
	}

	//fmt.Printf("gcc: %v\n", m)
	m = strings.Split(m[1], ".")
	major := m[0]
	minor := m[1]
	vers := fmt.Sprintf("gcc%s%s", major, minor)
	return vers, nil
}

func (ctx *Context) infer_cmtcfg(pinfos platform.Platform, hwaf_arch, hwaf_os, hwaf_comp string) (string, error) {

	var err error
	var cmtcfg string

	hwaf_os = pinfos.DistId()

	switch pinfos.System {
	case "Linux":
		hwaf_comp, err = infer_gcc_version()
		if err != nil {
			hwaf_comp = "gcc"
			err = nil
		}
		switch pinfos.DistName {
		case "centos", "sl", "slc", "rh", "rhel":
			rel := strings.Split(pinfos.DistVers, ".")
			major := rel[0]
			hwaf_os = pinfos.DistName + major

		case "ubuntu":
			vers := strings.Replace(pinfos.DistVers, ".", "", -1)
			hwaf_os = pinfos.DistName + vers

		case "arch":
			hwaf_os = "archlinux"

		default:
			ctx.Warn("hwaf: unhandled distribution [%s]\n", pinfos.DistId())
			hwaf_os = "linux"
			hwaf_comp = "gcc"
		}

	case "Darwin":
		rel := strings.Split(pinfos.DistVers, ".")
		major := rel[0]
		minor := rel[1]
		hwaf_os = pinfos.DistName + major + minor
		if strings.HasPrefix(pinfos.DistVers, "10.6") {
			hwaf_comp, err = infer_gcc_version()
			if err != nil {
				hwaf_comp = "gcc"
			}
		} else if strings.HasPrefix(pinfos.DistVers, "10.7") {
			hwaf_comp = "clang41"
		} else if strings.HasPrefix(pinfos.DistVers, "10.8") {
			hwaf_comp = "clang41"
		} else {
			panic(fmt.Sprintf("hwaf: unhandled distribution [%s]", pinfos.DistId()))
		}

	default:
		panic(fmt.Sprintf("hwaf: unknown platform [%s]", pinfos.System))
	}

	cmtcfg = fmt.Sprintf("%s-%s-%s-opt", hwaf_arch, hwaf_os, hwaf_comp)
	return cmtcfg, err
}

func hwaf_root() string {
	v := os.Getenv("HWAF_ROOT")
	if v != "" && path_exists(v) {
		return v
	}

	// check if we have the expected structure:
	//  /top/dir/bin/hwaf (this executable)
	//          /share/hwaf
	exe, err := exec.LookPath(os.Args[0])
	if err != nil {
		// impossible ?
		panic(err.Error())
	}

	bin, err := filepath.Abs(filepath.Dir(exe))
	if err == nil {
		root := filepath.Dir(bin)
		share := filepath.Join(root, "share", "hwaf")
		if path_exists(root) && path_exists(share) {
			return root
		}
	}

	return ""
}

func (ctx *Context) load_env_from_cfg(cfg *gocfg.Config) error {

	if !cfg.HasSection("hwaf-env") {
		return nil
	}

	section := "hwaf-env"
	options, err := cfg.Options(section)
	if err != nil {
		return err
	}
	for _, k := range options {
		v, err := cfg.String(section, k)
		if err != nil {
			continue
		}
		v = os.ExpandEnv(v)

		vv := os.Getenv(k)
		if vv != "" && vv != v {
			// we don't override parent environment!
			// would be too confusing
			ctx.Warn(
				"configuration tries to override env.var [%s] with [%s] (current=%s)\n",
				k, v, vv,
			)
		}
		err = os.Setenv(k, v)
		if err != nil {
			ctx.Warn("problem setting env. var [%s]: %v\n", k, err)
		}
	}
	return nil
}

func (ctx *Context) init() error {
	var err error
	root := hwaf_root()
	if root == "" {
		//return ErrNoHwafRootDir
	}
	ctx.Root = root

	ctx.gcfg, err = ctx.GlobalCfg()
	if err != nil {
		return err
	}

	// configure environment
	err = ctx.load_env_from_cfg(ctx.gcfg)
	if err != nil {
		return fmt.Errorf("hwaf: problem loading environment from global config: %v", err)
	}

	ctx.lcfg, err = ctx.LocalCfg()
	if ctx.lcfg != nil {
		err = ctx.load_env_from_cfg(ctx.lcfg)
		if err != nil {
			return fmt.Errorf("hwaf: problem loading environment from local config:\n%v", err)
		}
	}

	setup_env := func(topdir string) error {
		topdir = os.ExpandEnv(topdir)
		if !path_exists(topdir) {
			return nil
		}
		// add hepwaf-tools to the python environment
		pypath := os.Getenv("PYTHONPATH")
		hwaftools := ""
		if topdir == ctx.Root {
			hwaftools = filepath.Join(topdir, "share", "hwaf", "tools")
		} else {
			hwaftools = filepath.Join(topdir, "tools")
		}
		if !path_exists(hwaftools) {
			return fmt.Errorf("hwaf: no such directory [%s]", hwaftools)
		}
		if pypath == "" {
			pypath = hwaftools
		} else {
			pypath = pypath + string(os.PathListSeparator) + hwaftools
		}

		// detect the python version we are running
		py_version := "2"
		{
			py := os.Getenv("PYTHON")
			if py == "" {
				py = "python"
			}
			cmd := exec.Command(
				py,
				"-c", "import sys; print (sys.version_info[0])",
			)
			bout, err := cmd.Output()
			if err != nil {
				return fmt.Errorf("hwaf: could not detect python version: %v", err)
			}
			py_version = strings.Trim(string(bout), " \r\n")
			if py_version == "" {
				py_version = "2"
			}
		}
		py_dir := "py" + py_version
		if path_exists(filepath.Join(hwaftools, py_dir)) {
			pypath = pypath + string(os.PathListSeparator) + filepath.Join(hwaftools, py_dir)
			pypath = pypath + string(os.PathListSeparator) + filepath.Join(hwaftools, py_dir, "yaml")
		}
		os.Setenv("PYTHONPATH", pypath)

		// add the git-tools to the environment
		binpath := os.Getenv("PATH")
		hwafbin := filepath.Join(topdir, "bin")
		if !path_exists(hwafbin) {
			return fmt.Errorf("hwaf: no such directory [%s]", hwafbin)
		}

		if binpath == "" {
			binpath = hwafbin
		} else {
			binpath = binpath + string(os.PathListSeparator) + hwafbin
		}
		os.Setenv("PATH", binpath)
		return nil
	}

	// setup environment.
	// order matters:
	//   first one wins (as we append to the xyzPATH)
	err = setup_env(filepath.Join("${HOME}", ".config", "hwaf"))
	if err != nil {
		// ok... discard.
	}

	err = setup_env(ctx.Root)
	if err != nil {
		// this one is more critical
		return err
	}

	// FIXME: get sitedir from globalcfg and/or localcfg.
	ctx.sitedir = os.Getenv("HWAF_SITEDIR")
	if ctx.sitedir == "" {
		sitedir := filepath.Join(string(os.PathSeparator), "opt", "sw")
		//ctx.Warn("no $HWAF_SITEDIR env. variable. will use [%s]\n", sitedir)
		ctx.sitedir = sitedir
	}

	// init cmtcfg
	// FIXME: also get it from globalcfg/localcfg
	if ctx.cmtcfg == "" {
		if cmtcfg := os.Getenv("CMTCFG"); cmtcfg != "" {
			ctx.cmtcfg = cmtcfg
		} else {
			ctx.cmtcfg = ctx.DefaultCmtcfg()
		}
	}

	// init local pkg db
	_, _ = ctx.Workarea()
	if ctx.workarea != nil {
		fname := filepath.Join(*ctx.workarea, ".hwaf", "pkgdb.json")
		ctx.PkgDb = NewPackageDb(fname)
		if path_exists(fname) {
			err = ctx.PkgDb.Load(fname)
			if err != nil {
				return err
			}
		}
	}
	return err
}

func (ctx *Context) GlobalCfg() (*gocfg.Config, error) {
	var err error
	if ctx.gcfg != nil {
		return ctx.gcfg, nil
	}

	gcfg := gocfg.NewDefault()
	// aggregate all configurations. last one wins.
	for _, fname := range []string{
		filepath.Join(string(os.PathSeparator), "etc", "hwaf.conf"),
		filepath.Join(ctx.Root, "etc", "hwaf.conf"),
		filepath.Join("${HOME}", ".config", "hwaf.conf"),
	} {
		fname = os.ExpandEnv(fname)
		if !path_exists(fname) {
			continue
		}
		cfg, err := gocfg.ReadDefault(fname)
		if err != nil {
			return nil, err
		}
		for _, section := range cfg.Sections() {
			if !gcfg.HasSection(section) {
				if !gcfg.AddSection(section) {
					err = fmt.Errorf("hwaf: could not add section [%s] to global config", section)
					return nil, err
				}
			}
			options, err := cfg.Options(section)
			if err != nil {
				return nil, err
			}
			for _, option := range options {
				if gcfg.HasOption(section, option) {
					if !gcfg.RemoveOption(section, option) {
						err = fmt.Errorf("hwaf: could not remove option [%s] from section [%s] from global config", option, section)
						return nil, err
					}
				}
				v, err := cfg.RawString(section, option)
				if err != nil {
					return nil, err
				}
				if !gcfg.AddOption(section, option, v) {
					err = fmt.Errorf("hwaf: could not add option [%s] in section [%s] in global config (value=%s)", option, section, v)
					return nil, err
				}
			}
		}
	}

	ctx.gcfg = gcfg
	return ctx.gcfg, err
}

func (ctx *Context) LocalCfg() (*gocfg.Config, error) {

	workdir, err := ctx.Workarea()
	if err != nil {
		return nil, err
	}

	cfg_fname := filepath.Join(workdir, ".hwaf", "local.conf")
	if !path_exists(cfg_fname) {
		err = fmt.Errorf("could not find local config [%s]", cfg_fname)
		return nil, err
	}

	ctx.lcfg, err = gocfg.ReadDefault(cfg_fname)

	return ctx.lcfg, err
}

func (ctx *Context) Warn(format string, args ...interface{}) (n int, err error) {
	return fmt.Fprintf(os.Stderr, "hwaf: "+format, args...)
}

// EOF
