package main

import (
	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
	//gocfg "github.com/gonuts/config"
)

func hwaf_make_cmd_waf_show() *commander.Commander {
	cmd := &commander.Commander{
		Name:  "show",
		Short: "show informations about packages and projects",
		Commands: []*commander.Command{
			hwaf_make_cmd_waf_show_active_tags(),
			hwaf_make_cmd_waf_show_cmtcfg(),
			hwaf_make_cmd_waf_show_constituents(),
			hwaf_make_cmd_waf_show_default_cmtcfg(),
			hwaf_make_cmd_waf_show_flags(),
			hwaf_make_cmd_waf_show_platform(),
			hwaf_make_cmd_waf_show_projects(),
			hwaf_make_cmd_waf_show_project_name(),
			hwaf_make_cmd_waf_show_project_version(),
			hwaf_make_cmd_waf_show_pkg_uses(),
			hwaf_make_cmd_waf_show_pkg_tree(),
			hwaf_make_cmd_waf_show_setup(),
		},
		Flag: flag.NewFlagSet("hwaf-show", flag.ExitOnError),
	}
	return cmd
}

// EOF
