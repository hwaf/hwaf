package main

import (
	"fmt"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
)

func hwaf_make_cmd_waf_show_variant() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_waf_show_variant,
		UsageLine: "variant",
		Short:     "show local project's HWAF_VARIANT value",
		Long: `
show variant displays the project's HWAF_VARIANT value.

ex:
 $ hwaf show variant
 x86_64-linux-gcc-opt
`,
		Flag: *flag.NewFlagSet("hwaf-waf-show-variant", flag.ExitOnError),
	}
	return cmd
}

func hwaf_run_cmd_waf_show_variant(cmd *commander.Command, args []string) {
	var err error
	//n := "hwaf-" + cmd.Name()

	pinfo, err := g_ctx.ProjectInfos()
	handle_err(err)
	variant, err := pinfo.Get("HWAF_VARIANT")
	handle_err(err)

	fmt.Printf("%s\n", variant)
}

// EOF
