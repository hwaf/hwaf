package main

import (
	"os"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
)

func hwaf_make_cmd_waf_run() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_waf_run,
		UsageLine: "run",
		Short:     "run a command with the correct (project) environment",
		Long: `
run a command with the correct (project) environment.

ex:
 $ hwaf run some-command --some-flag some-data
`,
		Flag:        *flag.NewFlagSet("hwaf-waf-run", flag.ExitOnError),
		CustomFlags: true,
	}
	return cmd
}

func hwaf_run_cmd_waf_run(cmd *commander.Command, args []string) error {
	var err error
	//n := "hwaf-" + cmd.Name()

	waf, err := g_ctx.WafBin()
	if err != nil {
		return err
	}

	pwd, err := os.Getwd()
	if err != nil {
		return err
	}

	err = os.Setenv("HWAF_WAF_SHELL_CWD", pwd)
	if err != nil {
		return err
	}

	subargs := append([]string{"run", "--"}, args...)
	sub := g_ctx.Command(waf, subargs...)
	sub.Stdin = os.Stdin
	sub.Stdout = os.Stdout
	sub.Stderr = os.Stderr
	return sub.Run()
}

// EOF
