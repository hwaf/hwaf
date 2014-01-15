package main

import (
	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
	//gocfg "github.com/gonuts/config"
)

func hwaf_make_cmd_pkg() *commander.Command {
	cmd := &commander.Command{
		UsageLine: "pkg [options]",
		Short: "add, remove or inspect sub-packages",
		Subcommands: []*commander.Command{
			hwaf_make_cmd_pkg_add(),
			hwaf_make_cmd_pkg_create(),
			hwaf_make_cmd_pkg_ls(),
			hwaf_make_cmd_pkg_rm(),
		},
		Flag: *flag.NewFlagSet("hwaf-pkg", flag.ExitOnError),
	}
	return cmd
}

// EOF
