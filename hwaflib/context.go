package hwaflib

import (
	"bytes"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"os/signal"
	"path/filepath"
	"regexp"
	"runtime"
	"strings"

	gocfg "github.com/gonuts/config"
	"github.com/gonuts/logger"
	"github.com/hwaf/gas"
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
	Root     string         // top-level directory of the hwaf installation
	sitedir  string         // top-level directory for s/w installation
	variant  string         // current Variant
	workarea *string        // work directory for a local checkout
	gcfg     *gocfg.Config  // the global configuration (user>global)
	lcfg     *gocfg.Config  // the local config of a local workarea
	PkgDb    *PackageDb     // a naive database of locally checked out packages
	msg      *logger.Logger // for messaging
	subcmds  []*exec.Cmd    // list of subcommands launched by hwaf
	atexit   []func()       // list of functions to run at-exit
}

func NewContext() (*Context, error) {
	var err error
	var ctx *Context

	ctx = &Context{
		Root:     "",
		sitedir:  "",
		variant:  "",
		workarea: nil,
		gcfg:     nil,
		lcfg:     nil,
		PkgDb:    nil,
		msg:      logger.New("hwaf"),
		subcmds:  make([]*exec.Cmd, 0),
		atexit:   make([]func(), 0),
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
		variant:  "",
		workarea: &wdir,
		gcfg:     nil,
		lcfg:     nil,
		PkgDb:    nil,
		msg:      logger.New("hwaf"),
		subcmds:  make([]*exec.Cmd, 0),
		atexit:   make([]func(), 0),
	}

	err = ctx.init()
	return ctx, err
}

// Exit runs the at-exit functions before calling os.Exit
func (ctx *Context) Exit(rc int) {
	for _, fct := range ctx.atexit {
		fct()
	}
	os.Exit(rc)
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
		err = ctx.init_waf_ctx()
		if err != nil {
			ctx.Warnf("problem initializing waf: %v\n", err)
			return "", err
		}
		return waf, nil
	}

	top = ctx.Root
	waf = filepath.Join(top, "bin", "waf")
	if path_exists(waf) {
		err = ctx.init_waf_ctx()
		if err != nil {
			ctx.Warnf("problem initializing waf: %v\n", err)
			return "", err
		}
		return waf, nil
	}

	return "", fmt.Errorf("could not find 'waf' binary")
}

func (ctx *Context) Sitedir() string {
	return ctx.sitedir
}

func (ctx *Context) Variant() string {
	return ctx.variant
}

func (ctx *Context) pkgdir() string {
	if ctx.lcfg == nil {
		return "src"
	}
	pkgdir, err := ctx.lcfg.String("hwaf-cfg", "pkgdir")
	if err != nil {
		return "src"
	}
	return pkgdir
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

func (ctx *Context) DefaultVariant() string {
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
	variant := fmt.Sprintf("%s-%s-%s-opt", hwaf_arch, hwaf_os, hwaf_comp)

	pinfos, err := platform.Infos()
	if err != nil {
		//println("*** error:" + err.Error())
		return variant
	}

	// try harder...
	variant2, err := ctx.infer_variant(pinfos, hwaf_arch, hwaf_os, hwaf_comp)
	if err != nil {
		//println("*** error:" + err.Error())
		return variant
	}
	variant = variant2
	return variant
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

func (ctx *Context) infer_variant(pinfos platform.Platform, hwaf_arch, hwaf_os, hwaf_comp string) (string, error) {

	var err error
	var variant string

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
			ctx.Warnf("hwaf: unhandled distribution [%s]\n", pinfos.DistId())
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
		} else if strings.HasPrefix(pinfos.DistVers, "10.9") {
			hwaf_comp = "clang50"
		} else {
			panic(fmt.Sprintf("hwaf: unhandled distribution [%s]", pinfos.DistId()))
		}

	default:
		panic(fmt.Sprintf("hwaf: unknown platform [%s]", pinfos.System))
	}

	variant = fmt.Sprintf("%s-%s-%s-opt", hwaf_arch, hwaf_os, hwaf_comp)
	return variant, err
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
			ctx.Warnf(
				"configuration tries to override env.var [%s] with [%s] (current=%s)\n",
				k, v, vv,
			)
		}
		err = os.Setenv(k, v)
		if err != nil {
			ctx.Warnf("problem setting env. var [%s]: %v\n", k, err)
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

	// initialize signal handler
	go func() {
		ch := make(chan os.Signal)
		signal.Notify(ch, os.Interrupt, os.Kill)
		for {
			select {
			case sig := <-ch:
				// fmt.Fprintf(os.Stderr, "\n>>>>>>>>>\ncaught %#v\n", sig)
				// fmt.Fprintf(os.Stderr, "subcmds: %d %#v\n", len(ctx.subcmds), ctx.subcmds)
				for _, cmd := range ctx.subcmds {
					// fmt.Fprintf(os.Stderr, ">>> icmd %d...\n", icmd)
					if cmd == nil {
						// fmt.Fprintf(os.Stderr, ">>> cmd nil\n")
						continue
					}
					// fmt.Fprintf(os.Stderr, ">>> sync-ing\n")
					if stdout, ok := cmd.Stdout.(interface {
						Sync() error
					}); ok {
						stdout.Sync()
					}
					if stderr, ok := cmd.Stderr.(interface {
						Sync() error
					}); ok {
						stderr.Sync()
					}
					proc := cmd.Process
					if proc == nil {
						continue
					}
					// fmt.Fprintf(os.Stderr, ">>> signaling...\n")
					_ = proc.Signal(sig)
					// fmt.Fprintf(os.Stderr, ">>> signaling... [done]\n")
					ps, pserr := proc.Wait()
					if pserr != nil {
						// fmt.Fprintf(os.Stderr, "waited and got: %#v\n", pserr)
					} else {
						if !ps.Exited() {
							// fmt.Fprintf(os.Stderr, ">>> killing...\n")
							proc.Kill()
							// fmt.Fprintf(os.Stderr, ">>> killing... [done]\n")
						}
					}
					if stdout, ok := cmd.Stdout.(interface {
						Sync() error
					}); ok {
						stdout.Sync()
					}
					if stderr, ok := cmd.Stderr.(interface {
						Sync() error
					}); ok {
						stderr.Sync()
					}
					// fmt.Fprintf(os.Stderr, ">>> re-sync-ing... [done]\n")
				}
				// fmt.Fprintf(os.Stderr, "flushing\n")
				_ = os.Stderr.Sync()
				_ = os.Stdout.Sync()
				// fmt.Fprintf(os.Stderr, "flushed\n")
				ctx.Exit(1)
				return
			}
		}
	}()

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
	if ctx.lcfg != nil && err == nil {
		err = ctx.load_env_from_cfg(ctx.lcfg)
		if err != nil {
			return fmt.Errorf("hwaf: problem loading environment from local config:\n%v", err)
		}
	}
	err = nil

	// load local config
	if ctx.lcfg != nil {
		ctx.variant, err = ctx.lcfg.String("hwaf-cfg", "variant")
		if err != nil {
			err = nil
			ctx.variant = ""
		}
	}

	setup_env := func(topdir string) error {
		topdir = os.ExpandEnv(topdir)
		if !path_exists(topdir) {
			return fmt.Errorf("hwaf: no such directory [%s]", topdir)
		}
		// add hepwaf-tools to the python environment
		pypath := os.Getenv("PYTHONPATH")
		pyhwafdir := ""
		if topdir == ctx.Root {
			pyhwafdir = filepath.Join(topdir, "share", "hwaf", "tools")
		} else {
			pyhwafdir = filepath.Join(topdir, "py-hwaftools")
		}
		if !path_exists(pyhwafdir) {
			return fmt.Errorf("hwaf: no such directory [%s]", pyhwafdir)
		}
		hwaftools := strings.Join(
			[]string{
				pyhwafdir,
				filepath.Join(pyhwafdir, "orch"),
			},
			string(os.PathListSeparator),
		)
		if pypath == "" {
			pypath = hwaftools
		} else {
			pypath = pypath + string(os.PathListSeparator) + hwaftools
		}

		os.Setenv("PYTHONPATH", pypath)
		os.Setenv("HWAF_VERSION", ctx.Version())
		os.Setenv("HWAF_REVISION", ctx.Revision())
		return nil
	}

	// setup environment.
	// order matters:
	switch ctx.Root {
	default:
		err = setup_env(ctx.Root)
		if err != nil {
			return err
		}
	case "":
		topdir, err := gas.Abs("github.com/hwaf/hwaf")
		if err != nil {
			return err
		}
		err = setup_env(topdir)
		if err != nil {
			return err
		}
	}

	// FIXME: get sitedir from globalcfg and/or localcfg.
	ctx.sitedir = os.Getenv("HWAF_SITEDIR")
	if ctx.sitedir == "" {
		sitedir := filepath.Join(string(os.PathSeparator), "opt", "sw")
		//ctx.Warn("no $HWAF_SITEDIR env. variable. will use [%s]\n", sitedir)
		ctx.sitedir = sitedir
	}

	// init variant
	// FIXME: also get it from globalcfg/localcfg
	if ctx.variant == "" {
		if variant := os.Getenv("HWAF_VARIANT"); variant != "" {
			ctx.variant = variant
		} else {
			ctx.variant = ctx.DefaultVariant()
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
		filepath.Join("${HOME}", ".config", "hwaf", "local.conf"),
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

	cfg_fname := filepath.Join(workdir, "local.conf")
	if !path_exists(cfg_fname) {
		err = fmt.Errorf("could not find local config [%s]", cfg_fname)
		return nil, err
	}

	ctx.lcfg, err = gocfg.ReadDefault(cfg_fname)

	return ctx.lcfg, err
}

// ProjectInfos returns the ProjectInfos for the current context.
func (ctx *Context) ProjectInfos() (*ProjectInfos, error) {

	workdir, err := ctx.Workarea()
	if err != nil {
		return nil, err
	}

	// FIXME: get actual value from waf, somehow
	pinfo_name := filepath.Join(workdir, "__build__", "c4che", "_cache.py")
	if !path_exists(pinfo_name) {
		err = fmt.Errorf(
			"no such file [%s]. did you run \"hwaf configure\" ?",
			pinfo_name,
		)
		return nil, err
	}

	return NewProjectInfos(pinfo_name)
}

func (ctx *Context) SetMsgLevel(lvl logger.Level) {
	ctx.msg.SetLevel(lvl)
}

func (ctx *Context) Debugf(format string, args ...interface{}) (n int, err error) {
	return ctx.msg.Debugf(format, args...)
}

func (ctx *Context) Infof(format string, args ...interface{}) (n int, err error) {
	return ctx.msg.Infof(format, args...)
}

func (ctx *Context) Warnf(format string, args ...interface{}) (n int, err error) {
	return ctx.msg.Warnf(format, args...)
}

func (ctx *Context) Errorf(format string, args ...interface{}) (n int, err error) {
	return ctx.msg.Errorf(format, args...)
}

// Command returns the os/exec.Cmd struct with some valid defaults
func (ctx *Context) Command(name string, arg ...string) *exec.Cmd {
	// fmt.Printf(">>>> command [%s]... %#v\n", name, arg)
	cmd := exec.Command(name, arg...)
	ctx.subcmds = append(ctx.subcmds, cmd)
	return cmd
}

// EOF
