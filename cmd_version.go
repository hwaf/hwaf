package main

import (
	"fmt"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
)

func hwaf_make_cmd_version() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_version,
		UsageLine: "version",
		Short:     "print version and exit",
		Long: `
print version and exit.

ex:
 $ hwaf version
 hwaf-20130808 (b0aa7e1)
`,
		Flag: *flag.NewFlagSet("hwaf-version", flag.ExitOnError),
	}
	return cmd
}

func hwaf_run_cmd_version(cmd *commander.Command, args []string) {
	fmt.Printf("hwaf-20130808 (b0aa7e1)\n")
}

// EOF
