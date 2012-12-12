package main

import (
	"fmt"
	"os"
	"path/filepath"

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
		fmt.Printf("**error**: %v\n", err.Error())
		os.Exit(1)
	}
}

func get_workarea_root() (string, error) {
	// FIXME: use git-root
	return os.Getwd()
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
// EOF
