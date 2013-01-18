package main

import (
	"os"
	"os/exec"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
)

func hwaf_make_cmd_waf_shell() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_waf_shell,
		UsageLine: "shell",
		Short:     "run an interactive shell with the correct environment",
		Long: `
run an interactive shell with the correct environment.

ex:
 $ hwaf shell
`,
		Flag:        *flag.NewFlagSet("hwaf-waf-shell", flag.ExitOnError),
		CustomFlags: true,
	}
	return cmd
}

func hwaf_run_cmd_waf_shell(cmd *commander.Command, args []string) {
	var err error
	//n := "hwaf-" + cmd.Name()

	waf, err := g_ctx.WafBin()
	handle_err(err)

	subargs := append([]string{"shell"}, args...)
	sub := exec.Command(waf, subargs...)
	sub.Stdin = os.Stdin
	sub.Stdout = os.Stdout
	sub.Stderr = os.Stderr
	err = sub.Run()
	handle_err(err)
}

// EOF
