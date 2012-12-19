package main

import (
	"fmt"
	// "os"
	// "os/exec"
	// "path/filepath"

	"github.com/sbinet/go-commander"
	"github.com/sbinet/go-flag"
)

func hwaf_make_cmd_waf_bdist() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_waf_bdist,
		UsageLine: "bdist [output-filename]",
		Short:     "create a binary distribution from the project or packages",
		Long: `
bdist create a binary distribution from the project or packages.

ex:
 $ hwaf bdist
 $ hwaf bdist mana-20121218
`,
		Flag:        *flag.NewFlagSet("hwaf-bdist", flag.ExitOnError),
	//CustomFlags: true,
	}
	cmd.Flag.Bool("q", false, "only print error and warning messages, all other output will be suppressed")
	return cmd
}

func hwaf_run_cmd_waf_bdist(cmd *commander.Command, args []string) {
	var err error
	n := "hwaf-" + cmd.Name()

	fname := ""
	switch len(args) {
	case 0:
		fname = ""
	case 1:
		fname = args[0]
	default:
		err = fmt.Errorf("%s: too many arguments (%d)", n, len(args))
		handle_err(err)
	}

	if fname == "" {
	}

	
}

// EOF
