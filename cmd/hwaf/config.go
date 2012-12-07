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
		if err != nil {
			panic(err.Error())
		}
	}

	fname := CfgFname

	if !path_exists(fname) {
		section := "hwaf"
		if !Cfg.AddSection(section) {
			err := fmt.Errorf("hwaf: could not create section [%s] in file [%s]", section, fname)
			panic(err.Error())
		}
		err := Cfg.WriteFile(CfgFname, 0600, "")
		if err != nil {
			panic(err.Error())
		}
	} else {
		cfg, err := gocfg.ReadDefault(fname)
		if err != nil {
			panic(err.Error())
		}
		Cfg = cfg
	}
}

// EOF
