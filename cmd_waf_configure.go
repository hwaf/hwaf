package main

import (
	"os"
	"os/exec"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
)

func hwaf_make_cmd_waf_configure() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_waf_configure,
		UsageLine: "configure",
		Short:     "configure local project or packages",
		Long: `
configure configures the local project or packages.

ex:
 $ hwaf configure
 $ hwaf configure --prefix=my-install-area
 $ hwaf configure --prefix=my-install-area --with-clhep=/path/to/clhep
`,
		Flag:        *flag.NewFlagSet("hwaf-waf-configure", flag.ExitOnError),
		CustomFlags: true,
	}
	return cmd
}

func hwaf_run_cmd_waf_configure(cmd *commander.Command, args []string) {
	var err error
	//n := "hwaf-" + cmd.Name()

	waf, err := g_ctx.WafBin()
	handle_err(err)

	subargs := append([]string{"configure"}, args...)
	sub := exec.Command(waf, subargs...)
	sub.Stdout = os.Stdout
	sub.Stderr = os.Stderr
	err = sub.Run()
	handle_err(err)
}

// EOF
