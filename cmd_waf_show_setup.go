package main

import (
	"fmt"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
)

func hwaf_make_cmd_waf_show_setup() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_waf_show_setup,
		UsageLine: "setup",
		Short:     "show setup informations",
		Long: `
show setup displays the setup informations.

ex:
 $ hwaf show setup
`,
		Flag: *flag.NewFlagSet("hwaf-waf-show-setup", flag.ExitOnError),
	}
	return cmd
}

func hwaf_run_cmd_waf_show_setup(cmd *commander.Command, args []string) {
	var err error
	//n := "hwaf-" + cmd.Name()

	workdir, err := g_ctx.Workarea()
	if err != nil {
		workdir = "<N/A>"
	}
	fmt.Printf("workarea=%s\n", workdir)
	lconf, err := g_ctx.LocalCfg()
	if err != nil {
		handle_err(
			fmt.Errorf("%v\ndid you forget to run 'hwaf setup' ?", err),
		)
	}

	for _, k := range [][]string{
		{"hwaf-cfg", "variant"},
		{"hwaf-cfg", "projects"},
	} {
		section := k[0]
		option := k[1]
		v := ""
		v, err = lconf.String(section, option)
		if err != nil {
			v = "<N/A>"
		}
		fmt.Printf("%s=%s\n", option, v)
	}
}

// EOF
