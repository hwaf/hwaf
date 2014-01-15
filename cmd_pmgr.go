package main

import (
	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
)

func hwaf_make_cmd_pmgr() *commander.Command {
	cmd := &commander.Command{
		UsageLine: "pmgr [options]",
		Short: "query, download and install projects",
		Subcommands: []*commander.Command{
			hwaf_make_cmd_pmgr_get(),
		},
		Flag: *flag.NewFlagSet("hwaf-pmgr", flag.ExitOnError),
	}
	return cmd
}

// EOF
