package main

import (
	"fmt"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
)

func hwaf_make_cmd_waf_show_default_cmtcfg() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_waf_show_default_cmtcfg,
		UsageLine: "default-cmtcfg",
		Short:     "show local project's default CMTCFG value",
		Long: `
show default-cmtcfg displays the project's (default) CMTCFG value.

ex:
 $ hwaf show default-cmtcfg
 x86_64-slc6-gcc44-opt
`,
		Flag: *flag.NewFlagSet("hwaf-waf-show-default-cmtcfg", flag.ExitOnError),
	}
	return cmd
}

func hwaf_run_cmd_waf_show_default_cmtcfg(cmd *commander.Command, args []string) {
	fmt.Printf("%s\n", g_ctx.DefaultCmtcfg())
}

// EOF
