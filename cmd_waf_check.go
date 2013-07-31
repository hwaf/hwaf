package main

import (
	"os"
	"os/exec"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
)

func hwaf_make_cmd_waf_check() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_waf_check,
		UsageLine: "check",
		Short:     "check builds local project or packages and runs unit-tests",
		Long: `
check builds the local project or packages and runs unit-tests

ex:
 $ hwaf check
`,
		Flag:        *flag.NewFlagSet("hwaf-waf-check", flag.ExitOnError),
		CustomFlags: true,
	}
	return cmd
}

func hwaf_run_cmd_waf_check(cmd *commander.Command, args []string) {
	var err error
	//n := "hwaf-" + cmd.Name()

	waf, err := g_ctx.WafBin()
	handle_err(err)

	subargs := append([]string{"build", "--alltests"}, args...)
	sub := exec.Command(waf, subargs...)
	sub.Stdout = os.Stdout
	sub.Stderr = os.Stderr
	err = sub.Run()
	handle_err(err)
}

// EOF
