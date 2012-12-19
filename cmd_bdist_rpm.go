package main

import (
	"fmt"
	// "io"
	// "io/ioutil"
	// "os"
	// "os/exec"
	// "path/filepath"
	// "strings"

	"github.com/sbinet/go-commander"
	"github.com/sbinet/go-flag"
)

func hwaf_make_cmd_waf_bdist_rpm() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_waf_bdist_rpm,
		UsageLine: "bdist-rpm [rpm-name]",
		Short:     "create a RPM from the local project/packages",
		Long: `
bdist-rpm creates a RPM from the local project/packages.

ex:
 $ hwaf bdist-rpm
 $ hwaf bdist-rpm mana-20121218
`,
		Flag: *flag.NewFlagSet("hwaf-bdist-rpm", flag.ExitOnError),
	}
	cmd.Flag.Bool("q", false, "only print error and warning messages, all other output will be suppressed")
	return cmd
}

func hwaf_run_cmd_waf_bdist_rpm(cmd *commander.Command, args []string) {
	var err error
	n := "hwaf-" + cmd.Name()

	fname := ""

	switch len(args) {
	case 0:
		fname = ""
	case 1:
		fname = args[0]
	default:
		err = fmt.Errorf("%s: too many arguments (%s)", n, len(args))
		handle_err(err)
	}

	quiet := cmd.Flag.Lookup("q").Value.Get().(bool)

	if fname == "" {
	}

	if !quiet {
		fmt.Printf("%s: building RPM [%s]...\n", n, fname)
	}

	if !quiet {
		fmt.Printf("%s: building RPM [%s]...[ok]\n", n, fname)
	}
}

// EOF
