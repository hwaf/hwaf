package main

import (
	"fmt"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
)

func hwaf_make_cmd_waf_show_project_version() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_waf_show_project_version,
		UsageLine: "project-version",
		Short:     "show local project's version",
		Long: `
show project-version displays the project's version.

ex:
 $ hwaf show project-version
 0.0.1
`,
		Flag: *flag.NewFlagSet("hwaf-waf-show-project-version", flag.ExitOnError),
	}
	return cmd
}

func hwaf_run_cmd_waf_show_project_version(cmd *commander.Command, args []string) error {
	var err error
	//n := "hwaf-" + cmd.Name()

	pinfo, err := g_ctx.ProjectInfos()
	if err != nil {
		return err
	}
	val, err := pinfo.Get("HWAF_PROJECT_VERSION")
	if err != nil {
		return err
	}

	fmt.Printf("%s\n", val)

	return err
}

// EOF
