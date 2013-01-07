package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	//"strconv"
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

func handle_err(err error) {
	if err != nil {
		fmt.Fprintf(os.Stderr, "**error**: %v\n", err.Error())
		os.Exit(1)
	}
}

func get_workarea_root() (string, error) {
	// FIXME: handle case where we are invoked from a submodule directory
	git := exec.Command(
		"git", "rev-parse", "--show-toplevel",
	)
	bout, err := git.Output()
	if err != nil {
		return "", err
	}
	out := strings.Trim(string(bout), "\r\n")
	return filepath.Abs(out)
}

func get_default_cmtcfg() string {
	hwaf_os := runtime.GOOS
	hwaf_arch := runtime.GOARCH
	switch hwaf_arch {
	case "amd64":
		hwaf_arch = "x86_64"
	case "i386":
		hwaf_arch = "i686"
	default:
		//hwaf_arch = "unknown"
	}
	//FIXME: is 'gcc' a good enough default ?
	return fmt.Sprintf("%s-%s-gcc-opt", hwaf_arch, hwaf_os)
}

func load_local_cfg() *gocfg.Config {
	workdir, err := get_workarea_root()
	handle_err(err)

	cfg_fname := filepath.Join(workdir, ".hwaf", "local.cfg")
	if !path_exists(cfg_fname) {
		err = fmt.Errorf("could not find local config [%s]", cfg_fname)
		handle_err(err)
	}

	cfg, err := gocfg.ReadDefault(cfg_fname)
	handle_err(err)

	return cfg
}

func hwaf_root() string {
	return os.ExpandEnv(filepath.Join("${HOME}", ".config", "hwaf"))
}

func hwaf_setup_waf_env() {
	py := os.Getenv("PYTHONPATH")
	hwaf := filepath.Join(hwaf_root(), "tools")
	if py == "" {
		py = hwaf
	} else {
		py = hwaf + string(os.PathListSeparator) + py
	}
	os.Setenv("PYTHONPATH", py)
}

type ProjectInfo struct {
	cfg *gocfg.Config
}

func NewProjectInfo(name string) (*ProjectInfo, error) {
	var err error
	fname := filepath.Clean(name)
	if !path_exists(fname) {
		err = fmt.Errorf("could not find project info [%s]", fname)
		return nil, err
	}
	cfg, err := gocfg.ReadDefault(fname)
	if err != nil {
		return nil, err
	}
	//fmt.Printf("cfg [%s]\nsections: %s\n", fname, cfg.Sections())
	return &ProjectInfo{cfg}, nil
}

func (pi *ProjectInfo) Get(key string) (string, error) {
	s, err := pi.cfg.String("DEFAULT", key)

	// we can't use strconv.Unquote as these are python strings...
	if len(s) > 1 {
		slen := len(s) - 1
		s0 := string(s[0])
		s1 := string(s[slen])
		if (s0 == "'" && s1 == "'") || (s0 == `"` && s1 == `"`) {
			s = s[1:slen]
		}
	}
	return s, err
}

// EOF
