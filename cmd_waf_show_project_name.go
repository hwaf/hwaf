package main

import (
	"fmt"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
)

func hwaf_make_cmd_waf_show_project_name() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_waf_show_project_name,
		UsageLine: "project-name",
		Short:     "show local project's name",
		Long: `
show project-name displays the project's name.

ex:
 $ hwaf show project-name
 mana-core
`,
		Flag: *flag.NewFlagSet("hwaf-waf-show-project-name", flag.ExitOnError),
	}
	return cmd
}

func hwaf_run_cmd_waf_show_project_name(cmd *commander.Command, args []string) {
	var err error
	//n := "hwaf-" + cmd.Name()

	pinfo, err := g_ctx.ProjectInfos()
	handle_err(err)
	val, err := pinfo.Get("HWAF_PROJECT_NAME")
	handle_err(err)

	fmt.Printf("%s\n", val)
}

// EOF
