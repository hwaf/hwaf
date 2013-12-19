package main

import (
	"fmt"
	// "os"
	// "os/exec"
	// "path/filepath"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
)

func hwaf_make_cmd_waf_sdist() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_waf_sdist,
		UsageLine: "sdist [output-filename]",
		Short:     "create a source distribution from the project or packages",
		Long: `
sdist creates a source distribution from the project or packages.

ex:
 $ hwaf sdist
 $ hwaf sdist mana-20121218
`,
		Flag: *flag.NewFlagSet("hwaf-sdist", flag.ExitOnError),
		//CustomFlags: true,
	}
	cmd.Flag.Bool("v", false, "enable verbose output")
	return cmd
}

func hwaf_run_cmd_waf_sdist(cmd *commander.Command, args []string) error {
	var err error
	n := "hwaf-" + cmd.Name()

	fname := ""
	switch len(args) {
	case 0:
		fname = ""
	case 1:
		fname = args[0]
	default:
		return fmt.Errorf("%s: too many arguments (%d)", n, len(args))
	}

	if fname == "" {
	}

	return err
}

// EOF
