package main

import (
	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
	"github.com/hwaf/hwaf/plugins/asetup"
)

func hwaf_make_cmd_asetup() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_asetup,
		UsageLine: "asetup [options] <args>",
		Short:     "setup a workarea with Athena-like defaults",
		Long: `
asetup sets up a workarea with Athena-like defaults.

ex:
 $ mkdir my-work-area && cd my-work-area
 $ hwaf asetup
 $ hwaf asetup mana,20121207
 $ hwaf asetup mana 20121207
 $ hwaf asetup -arch=64    mana 20121207
 $ hwaf asetup -comp=gcc44 mana 20121207
 $ hwaf asetup -os=centos6 mana 20121207
 $ hwaf asetup -type=opt   mana 20121207
 $ hwaf asetup -variant=x86_64-slc6-gcc44-opt mana 20121207
 $ HWAF_VARIANT=x86_64-slc6-gcc44-opt \
   hwaf asetup mana 20121207
`,
		Flag: *flag.NewFlagSet("hwaf-setup", flag.ExitOnError),
	}
	//cmd.Flag.String("p", "", "List of paths to projects to setup against")
	//cmd.Flag.String("cfg", "", "Path to a configuration file")
	cmd.Flag.Bool("v", false, "enable verbose mode")
	cmd.Flag.String("arch", "", "explicit architecture to use (32/64)")
	cmd.Flag.String("comp", "", "explicit compiler name to use (ex: gcc44, clang32,...)")
	cmd.Flag.String("os", "", "explicit system name to use (ex: slc6, slc5, centos6, darwin106,...)")
	cmd.Flag.String("type", "", "explicit build variant to use (ex: opt/dbg)")
	cmd.Flag.String("variant", "", "explicit HWAF_VARIANT value to use")
	return cmd
}

func hwaf_run_cmd_asetup(cmd *commander.Command, args []string) error {
	return asetup.Run(g_ctx, cmd, args)
}

// EOF
