package main

import (
	"os"
	"os/exec"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
)

func hwaf_make_cmd_waf() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_waf,
		UsageLine: "waf",
		Short:     "run waf itself",
		Long: `
waf runs the waf binary.

ex:
 $ hwaf waf
 $ hwaf waf --help
`,
		Flag:        *flag.NewFlagSet("hwaf-waf", flag.ExitOnError),
		CustomFlags: true,
	}
	return cmd
}

func hwaf_run_cmd_waf(cmd *commander.Command, args []string) {
	var err error
	//n := "hwaf-" + cmd.Name()

	waf, err := g_ctx.WafBin()
	handle_err(err)

	if len(args) == 1 && args[0] == "build+install" {
		sub := exec.Command(waf, "build", "--notests")
		sub.Stdin = os.Stdin
		sub.Stdout = os.Stdout
		sub.Stderr = os.Stderr
		err = sub.Run()
		handle_err(err)

		sub = exec.Command(waf, "install")
		sub.Stdin = os.Stdin
		sub.Stdout = os.Stdout
		sub.Stderr = os.Stderr
		err = sub.Run()
		handle_err(err)

		return
	}
	subargs := append([]string{}, args...)
	sub := exec.Command(waf, subargs...)
	sub.Stdin = os.Stdin
	sub.Stdout = os.Stdout
	sub.Stderr = os.Stderr
	err = sub.Run()
	handle_err(err)
}

// EOF
