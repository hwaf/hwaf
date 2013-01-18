package hwaflib

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"

	gocfg "github.com/sbinet/go-config/config"
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

func hwaf_root() string {
	v := os.Getenv("HWAF_ROOT")
	if v != "" && path_exists(v) {
		return v
	}
	
	return os.ExpandEnv(filepath.Join("${HOME}", ".config", "hwaf"))
}

// Context holds the necessary context informations for a hwaf installation
type Context struct {
	Root string // top-level directory of the hwaf installation
	workarea *string // work directory for a local checkout
	cfg *gocfg.Config // the aggregated configuration (local>user>global)
}

func NewContext() (*Context, error) {
	var err error
	var ctx *Context

	ctx = &Context{
		Root: "",
		workarea: nil,
		cfg: nil,
	}

	err = ctx.init()
	return ctx, err
}

func NewContextFrom(workarea string) (*Context, error) {
	var err error
	var ctx *Context

	if !path_exists(workarea) {
		err = fmt.Errorf("no such directory [%s]", workarea)
		return nil, err
	}

	wdir := string(workarea)
	ctx = &Context{
		Root: "",
		workarea: &wdir,
		cfg: nil,
	}

	err = ctx.init()
	return ctx, err
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

func (ctx *Context) init() error {
	return nil
}

// EOF
