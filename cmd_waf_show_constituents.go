package main

import (
	"os"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
)

func hwaf_make_cmd_waf_show_constituents() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_waf_show_constituents,
		UsageLine: "constituents [options] [<package name> [<package-name> [...]]]",
		Short:     "show targets of a project or package",
		Long: `
show constituents displays the list of targets which will be built.

ex:
 $ hwaf show constituents
 $ hwaf show constituents Control/AthenaCommon
`,
		Flag:        *flag.NewFlagSet("hwaf-waf-show-constituents", flag.ExitOnError),
		CustomFlags: true,
	}
	return cmd
}

func hwaf_run_cmd_waf_show_constituents(cmd *commander.Command, args []string) {
	var err error
	//n := "hwaf-" + cmd.Name()

	waf, err := g_ctx.WafBin()
	handle_err(err)

	subargs := append([]string{"list"}, args...)
	sub := g_ctx.Command(waf, subargs...)
	sub.Stdout = os.Stdout
	sub.Stderr = os.Stderr
	err = sub.Run()
	handle_err(err)
}

// EOF
