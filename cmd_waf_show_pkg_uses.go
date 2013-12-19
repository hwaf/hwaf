package main

import (
	"os"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
)

func hwaf_make_cmd_waf_show_pkg_uses() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_waf_show_pkg_uses,
		UsageLine: "pkg-uses",
		Short:     "show local project's dependencies",
		Long: `
show pkg-uses displays the uses of a given package.

ex:
 $ hwaf show pkg-uses Control/AthenaCommon
`,
		Flag:        *flag.NewFlagSet("hwaf-waf-show-pkg-uses", flag.ExitOnError),
		CustomFlags: true,
	}
	return cmd
}

func hwaf_run_cmd_waf_show_pkg_uses(cmd *commander.Command, args []string) error {
	var err error
	//n := "hwaf-" + cmd.Name()

	waf, err := g_ctx.WafBin()
	if err != nil {
		return err
	}

	subargs := append([]string{"show-pkg-uses"}, args...)
	sub := g_ctx.Command(waf, subargs...)
	sub.Stdout = os.Stdout
	sub.Stderr = os.Stderr
	return sub.Run()
}

// EOF
