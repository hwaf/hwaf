package main

import (
	"fmt"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
)

func hwaf_make_cmd_waf_show_active_tags() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_waf_show_active_tags,
		UsageLine: "active-tags [options]",
		Short:     "show list of active tags for the local project",
		Long: `
show list of active tags for the local project.

ex:
 $ hwaf show active-tags
 ['target-slc6', 'opt']

`,
		Flag: *flag.NewFlagSet("hwaf-waf-show-active-tags", flag.ExitOnError),
	}
	return cmd
}

func hwaf_run_cmd_waf_show_active_tags(cmd *commander.Command, args []string) error {
	var err error

	pinfo, err := g_ctx.ProjectInfos()
	if err != nil {
		return err
	}

	val, err := pinfo.Get("HWAF_ACTIVE_TAGS")
	if err != nil {
		return err
	}
	fmt.Printf("%s\n", val)

	return err
}

// EOF
