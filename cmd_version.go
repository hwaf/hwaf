package main

import (
	"fmt"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
)

func hwaf_make_cmd_version() *commander.Command {
	vers := g_ctx.Version()
	rev := g_ctx.Revision()
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_version,
		UsageLine: "version",
		Short:     "print version and exit",
		Long: fmt.Sprintf(`
print version and exit.

ex:
 $ hwaf version
 hwaf-%s (%s)
`, vers, rev),
		Flag: *flag.NewFlagSet("hwaf-version", flag.ExitOnError),
	}
	return cmd
}

func hwaf_run_cmd_version(cmd *commander.Command, args []string) error {
	vers := g_ctx.Version()
	rev := g_ctx.Revision()
	fmt.Printf("hwaf-%s (%s)\n", vers, rev)
	return nil
}

// EOF
