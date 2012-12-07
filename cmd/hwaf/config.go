package main

import (
	"fmt"
	"os"
	"path/filepath"

	gocfg "github.com/sbinet/go-config/config"
)

var Cfg = gocfg.NewDefault()
var CfgFname = os.ExpandEnv(filepath.Join("${HOME}", ".config", "hwaf", "config.ini"))

func init() {
	cfgdir := filepath.Dir(CfgFname)
	if !path_exists(cfgdir) {
		err := os.MkdirAll(cfgdir, 0700)
		handle_err(err)
	}

	fname := CfgFname

	if !path_exists(fname) {
		section := "hwaf"
		if !Cfg.AddSection(section) {
			err := fmt.Errorf("hwaf: could not create section [%s] in file [%s]", section, fname)
			handle_err(err)
		}
		err := Cfg.WriteFile(CfgFname, 0600, "")
		handle_err(err)
	} else {
		cfg, err := gocfg.ReadDefault(fname)
		handle_err(err)
		Cfg = cfg
	}
}

// EOF
