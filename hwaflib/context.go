package hwaflib

import (
	"errors"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"

	gocfg "github.com/sbinet/go-config/config"
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
	workarea *string       // work directory for a local checkout
	gcfg     *gocfg.Config // the global configuration (user>global)
	lcfg     *gocfg.Config // the local config of a local workarea
}

func NewContext() (*Context, error) {
	var err error
	var ctx *Context

	ctx = &Context{
		Root:     "",
		workarea: nil,
		gcfg:     nil,
		lcfg:     nil,
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
		workarea: &wdir,
		gcfg:     nil,
		lcfg:     nil,
	}

	err = ctx.init()
	return ctx, err
}

func (ctx *Context) WafBin() (string, error) {
	var err error

	top := ctx.Root
	waf := filepath.Join(top, "bin", "waf")
	if !path_exists(waf) {
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
	}
	return waf, err
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
	switch hwaf_arch {
	case "amd64":
		hwaf_arch = "x86_64"
	case "i386":
		hwaf_arch = "i686"
	default:
		//hwaf_arch = "unknown"
		panic(fmt.Sprintf("unknown architecture [%s]", hwaf_arch))
	}
	//FIXME: is 'gcc' a good enough default ?
	return fmt.Sprintf("%s-%s-gcc-opt", hwaf_arch, hwaf_os)
}

func hwaf_root() string {
	v := os.Getenv("HWAF_ROOT")
	if v != "" && path_exists(v) {
		return v
	}

	// check if we have the expected structure:
	//  /top/dir/bin/hwaf (this executable)
	//          /share/hwaf
	bin := filepath.Dir(os.Args[0])
	root := filepath.Dir(bin)
	share := filepath.Join(root, "share", "hwaf")
	if path_exists(root) && path_exists(share) {
		return root
	}

	return ""
}

func (ctx *Context) init() error {
	var err error
	root := hwaf_root()
	if root == "" {
		return ErrNoHwafRootDir
	}
	ctx.Root = root

	_, err = ctx.GlobalCfg()
	if err != nil {
		return err
	}

	// first one wins (as we append to the xyzPATH)
	for _, top := range []string{
		filepath.Join("${HOME}", ".config", "hwaf"),
		ctx.Root,
	} {
		top = os.ExpandEnv(top)
		if !path_exists(top) {
			continue
		}
		// add hepwaf-tools to the python environment
		pypath := os.Getenv("PYTHONPATH")
		hwaftools := filepath.Join(top, "share", "hwaf", "tools")
		if !path_exists(hwaftools) {
			return fmt.Errorf("hwaf: no such directory [%s]", hwaftools)
		}
		if pypath == "" {
			pypath = hwaftools
		} else {
			pypath = pypath + string(os.PathListSeparator) + hwaftools
		}
		os.Setenv("PYTHONPATH", pypath)

		// add the git-tools to the environment
		binpath := os.Getenv("PATH")
		hwafbin := filepath.Join(top, "bin")
		if !path_exists(hwafbin) {
			return fmt.Errorf("hwaf: no such directory [%s]", hwafbin)
		}

		if binpath == "" {
			binpath = hwafbin
		} else {
			binpath = binpath + string(os.PathListSeparator) + hwafbin
		}
		os.Setenv("PATH", binpath)
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
		filepath.Join("", "etc", "hwaf.conf"),
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
					err = fmt.Errorf("hwaf: could nit add option [%s] in section [%s] in global config (value=%s)", option, section, v)
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

	cfg_fname := filepath.Join(workdir, ".hwaf", "local.cfg")
	if !path_exists(cfg_fname) {
		err = fmt.Errorf("could not find local config [%s]", cfg_fname)
		return nil, err
	}

	ctx.lcfg, err = gocfg.ReadDefault(cfg_fname)

	return ctx.lcfg, err
}

// EOF
