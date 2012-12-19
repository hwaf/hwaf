package main

import (
	"github.com/sbinet/go-commander"
	"github.com/sbinet/go-flag"
	//gocfg "github.com/sbinet/go-config/config"
)

func hwaf_make_cmd_self() *commander.Commander {
	cmd := &commander.Commander{
	Name: "self",
	Short: "modify hwaf internal state",
	Commands: []*commander.Command{
			hwaf_make_cmd_self_init(),
			hwaf_make_cmd_self_update(),
		},
		Flag: flag.NewFlagSet("hwaf-self", flag.ExitOnError),
	}
	return cmd
}
// EOF
