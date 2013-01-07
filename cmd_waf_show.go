package main

import (
	"github.com/sbinet/go-commander"
	"github.com/sbinet/go-flag"
	//gocfg "github.com/sbinet/go-config/config"
)

func hwaf_make_cmd_waf_show() *commander.Commander {
	cmd := &commander.Commander{
		Name:  "show",
		Short: "show informations about packages and projects",
		Commands: []*commander.Command{
			hwaf_make_cmd_waf_show_cmtcfg(),
			hwaf_make_cmd_waf_show_projects(),
			hwaf_make_cmd_waf_show_project_name(),
			hwaf_make_cmd_waf_show_project_version(),
			hwaf_make_cmd_waf_show_pkg_uses(),
		},
		Flag: flag.NewFlagSet("hwaf-show", flag.ExitOnError),
	}
	return cmd
}

// EOF
