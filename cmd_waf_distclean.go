package main

import (
	"os"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
)

func hwaf_make_cmd_waf_distclean() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_waf_distclean,
		UsageLine: "distclean",
		Short:     "distclean local project or packages",
		Long: `
distclean removes the build directory of the local project or packages.

ex:
 $ hwaf distclean
`,
		Flag:        *flag.NewFlagSet("hwaf-waf-distclean", flag.ExitOnError),
		CustomFlags: true,
	}
	return cmd
}

func hwaf_run_cmd_waf_distclean(cmd *commander.Command, args []string) {
	var err error
	//n := "hwaf-" + cmd.Name()

	waf, err := g_ctx.WafBin()
	handle_err(err)

	subargs := append([]string{"distclean"}, args...)
	sub := g_ctx.Command(waf, subargs...)
	sub.Stdout = os.Stdout
	sub.Stderr = os.Stderr
	err = sub.Run()
	handle_err(err)
}

// EOF
