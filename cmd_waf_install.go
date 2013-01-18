package main

import (
	"os"
	"os/exec"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
)

func hwaf_make_cmd_waf_install() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_waf_install,
		UsageLine: "install",
		Short:     "install local project or packages",
		Long: `
install installs the local project or packages.

ex:
 $ hwaf install
 $ hwaf install --prefix=my-install-area
 $ hwaf install --prefix=my-install-area --destdir=/tmp/dest
`,
		Flag:        *flag.NewFlagSet("hwaf-waf-install", flag.ExitOnError),
		CustomFlags: true,
	}
	return cmd
}

func hwaf_run_cmd_waf_install(cmd *commander.Command, args []string) {
	var err error
	//n := "hwaf-" + cmd.Name()

	waf, err := g_ctx.WafBin()
	handle_err(err)

	subargs := append([]string{"install"}, args...)
	sub := exec.Command(waf, subargs...)
	sub.Stdout = os.Stdout
	sub.Stderr = os.Stderr
	err = sub.Run()
	handle_err(err)
}

// EOF
