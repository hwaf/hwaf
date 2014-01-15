package main

import (
	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
)

func hwaf_make_cmd_self() *commander.Command {
	cmd := &commander.Command{
		UsageLine: "self [options]",
		Short: "modify hwaf internal state",
		Subcommands: []*commander.Command{
			hwaf_make_cmd_self_init(),
			hwaf_make_cmd_self_bdist(),
			hwaf_make_cmd_self_bdist_upload(),
			hwaf_make_cmd_self_update(),
		},
		Flag: *flag.NewFlagSet("hwaf-self", flag.ExitOnError),
	}
	return cmd
}

// EOF
