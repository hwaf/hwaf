package main

import (
	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
	//gocfg "github.com/sbinet/go-config/config"
)

func hwaf_make_cmd_pmgr() *commander.Commander {
	cmd := &commander.Commander{
		Name:  "pmgr",
		Short: "query, download and install projects",
		Commands: []*commander.Command{
			hwaf_make_cmd_pmgr_get(),
		},
		Flag: flag.NewFlagSet("hwaf-pmgr", flag.ExitOnError),
	}
	return cmd
}

// EOF
