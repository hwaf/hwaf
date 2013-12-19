package main

import (
	"fmt"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
)

func hwaf_make_cmd_waf_show_default_variant() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_waf_show_default_variant,
		UsageLine: "default-variant",
		Short:     "show local project's default HWAF_VARIANT value",
		Long: `
show default-variant displays the project's (default) HWAF_VARIANT value.

ex:
 $ hwaf show default-variant
 x86_64-slc6-gcc44-opt
`,
		Flag: *flag.NewFlagSet("hwaf-waf-show-default-variant", flag.ExitOnError),
	}
	return cmd
}

func hwaf_run_cmd_waf_show_default_variant(cmd *commander.Command, args []string) error {
	fmt.Printf("%s\n", g_ctx.DefaultVariant())
	return nil
}

// EOF
