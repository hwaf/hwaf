package main

import (
	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
	//gocfg "github.com/gonuts/config"
)

func hwaf_make_cmd_git() *commander.Commander {
	cmd := &commander.Commander{
		Name:  "git",
		Short: "hwaf related git tools",
		Commands: []*commander.Command{
			hwaf_make_cmd_git_rm_submodule(),
			hwaf_make_cmd_git_svn_clone(),
		},
		Flag: flag.NewFlagSet("hwaf-git", flag.ExitOnError),
	}
	return cmd
}

// EOF
