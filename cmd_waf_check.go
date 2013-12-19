package main

import (
	"os"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
)

func hwaf_make_cmd_waf_check() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_waf_check,
		UsageLine: "check",
		Short:     "build and run unit-tests for the local project or packages",
		Long: `
check builds and runs unit-tests for the local project or packages.

ex:
 $ hwaf check
`,
		Flag:        *flag.NewFlagSet("hwaf-waf-check", flag.ExitOnError),
		CustomFlags: true,
	}
	return cmd
}

func hwaf_run_cmd_waf_check(cmd *commander.Command, args []string) error {
	var err error
	//n := "hwaf-" + cmd.Name()

	waf, err := g_ctx.WafBin()
	if err != nil {
		return err
	}

	subargs := append([]string{"build", "--alltests"}, args...)
	sub := g_ctx.Command(waf, subargs...)
	sub.Stdout = os.Stdout
	sub.Stderr = os.Stderr
	return sub.Run()
}

// EOF
