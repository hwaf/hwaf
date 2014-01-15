package main

import (
	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
)

func hwaf_make_cmd_waf_show() *commander.Command {
	cmd := &commander.Command{
		UsageLine: "show [options]",
		Short: "show informations about packages and projects",
		Subcommands: []*commander.Command{
			hwaf_make_cmd_waf_show_active_tags(),
			hwaf_make_cmd_waf_show_aliases(),
			hwaf_make_cmd_waf_show_constituents(),
			hwaf_make_cmd_waf_show_default_variant(),
			hwaf_make_cmd_waf_show_flags(),
			hwaf_make_cmd_waf_show_platform(),
			hwaf_make_cmd_waf_show_projects(),
			hwaf_make_cmd_waf_show_project_name(),
			hwaf_make_cmd_waf_show_project_version(),
			hwaf_make_cmd_waf_show_pkg_uses(),
			hwaf_make_cmd_waf_show_pkg_tree(),
			hwaf_make_cmd_waf_show_setup(),
			hwaf_make_cmd_waf_show_variant(),
		},
		Flag: *flag.NewFlagSet("hwaf-show", flag.ExitOnError),
	}
	return cmd
}

// EOF
