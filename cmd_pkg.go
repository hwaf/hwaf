package main

import (
	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
	//gocfg "github.com/sbinet/go-config/config"
)

func hwaf_make_cmd_pkg() *commander.Commander {
	cmd := &commander.Commander{
		Name:  "pkg",
		Short: "add, remove or inspect sub-packages",
		Commands: []*commander.Command{
			hwaf_make_cmd_pkg_add(),
			hwaf_make_cmd_pkg_create(),
			hwaf_make_cmd_pkg_ls(),
			hwaf_make_cmd_pkg_rm(),
		},
		Flag: flag.NewFlagSet("hwaf-pkg", flag.ExitOnError),
	}
	return cmd
}

// EOF
