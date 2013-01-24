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

	fmt.Printf("%s\n", pinfos)
}

// EOF
