package main

import (
	"os"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
)

func hwaf_make_cmd_waf_show_projects() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_waf_show_projects,
		UsageLine: "projects",
		Short:     "show local project's dependencies",
		Long: `
show project displays the project-dependency tree of the local project.

ex:
 $ hwaf show projects
`,
		Flag:        *flag.NewFlagSet("hwaf-waf-show-projects", flag.ExitOnError),
		CustomFlags: true,
	}
	return cmd
}

func hwaf_run_cmd_waf_show_projects(cmd *commander.Command, args []string) {
	var err error
	//n := "hwaf-" + cmd.Name()

	waf, err := g_ctx.WafBin()
	handle_err(err)

	subargs := append([]string{"show-projects"}, args...)
	sub := g_ctx.Command(waf, subargs...)
	sub.Stdout = os.Stdout
	sub.Stderr = os.Stderr
	err = sub.Run()
	handle_err(err)
}

// EOF
