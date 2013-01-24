package main

import (
	"fmt"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
	"github.com/mana-fwk/hwaf/platform"
)

func hwaf_make_cmd_waf_show_platform() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_waf_show_platform,
		UsageLine: "platform",
		Short:     "show platform informations",
		Long: `
show platform displays the platform informations.

ex:
 $ hwaf show platform
 Platform{Dist="slc-6.3" System="Linux" Node="voatlas04.cern.ch" Release="2.6.32-279.11.1.el6.x86_64" Version="#1 SMP Tue Oct 16 17:21:52 CEST 2012" Machine="x86_64" Processor="x86_64"}
`,
		Flag: *flag.NewFlagSet("hwaf-waf-show-platform", flag.ExitOnError),
	}
	return cmd
}

func hwaf_run_cmd_waf_show_platform(cmd *commander.Command, args []string) {
	var err error
	//n := "hwaf-" + cmd.Name()

	pinfos, err := platform.Infos()
	handle_err(err)

	fmt.Printf("%s\ndefault cmtcfg: %s\n", pinfos, g_ctx.DefaultCmtcfg())
}

// EOF
