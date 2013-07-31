package main

import (
	"os"
	"os/exec"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
)

func hwaf_make_cmd_waf_build() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_waf_build,
		UsageLine: "build",
		Short:     "build local project or packages",
		Long: `
build builds the local project or packages.

ex:
 $ hwaf build
 $ hwaf build --prefix=my-install-area
 $ hwaf build --prefix=my-install-area --destdir=/tmp/dest
`,
		Flag:        *flag.NewFlagSet("hwaf-waf-build", flag.ExitOnError),
		CustomFlags: true,
	}
	return cmd
}

func hwaf_run_cmd_waf_build(cmd *commander.Command, args []string) {
	var err error
	//n := "hwaf-" + cmd.Name()

	waf, err := g_ctx.WafBin()
	handle_err(err)

	subargs := []string{"build"}
	run_tests := false
	for _, arg := range args {
		if arg == "check" {
			arg = "--alltests"
			run_tests = true
		}
		subargs = append(subargs, arg)
	}
	if !run_tests {
		subargs = append(subargs[:1], append([]string{"--notests"}, subargs[1:]...)...)
	}

	sub := exec.Command(waf, subargs...)
	sub.Stdout = os.Stdout
	sub.Stderr = os.Stderr
	err = sub.Run()
	handle_err(err)
}

// EOF
