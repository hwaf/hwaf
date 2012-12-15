package main

import (
	"fmt"
	// "io"
	// "io/ioutil"
	// "os"
	// "os/exec"
	// "path"
	// "path/filepath"
	"strings"

	"github.com/sbinet/go-commander"
	"github.com/sbinet/go-flag"
)

func hwaf_make_cmd_pkgmgr_get() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_pkgmgr_get,
		UsageLine: "pkgmgr-get [options] <pkguri>",
		Short:     "download and install a package/project",
		Long: `
pkgmgr-get downloads and installs a package or project from a URI.

ex:
 $ hwaf pkgmgr-get cern.ch/mana-fwk/mana-latest
 $ hwaf pkgmgr-get -o /opt cern.ch/mana-fwk/mana-latest
`,
		Flag: *flag.NewFlagSet("hwaf-pkgmgr-get", flag.ExitOnError),
	}
	cmd.Flag.Bool("q", false, "only print error and warning messages, all other output will be suppressed")
	cmd.Flag.String("o", "", "directory where to install the package")
	return cmd
}

func hwaf_run_cmd_pkgmgr_get(cmd *commander.Command, args []string) {
	var err error
	n := "hwaf-" + cmd.Name()
	quiet := cmd.Flag.Lookup("q").Value.Get().(bool)

	pkguri := ""
	switch len(args) {
	case 1:
		pkguri = args[0]
	default:
		err = fmt.Errorf("%s: you need to give a package URI to install", n)
		handle_err(err)
	}

	
	pkguri = strings.Replace(pkguri, "http://", "", 1)
	pkguri = strings.Replace(pkguri, "https://", "", 1)

	if !quiet {
		fmt.Printf("%s: get [%s]...\n", n, pkguri)
	}

	//manifest_url := path.Join(pkguri, "MANIFEST")

	if !quiet {
		fmt.Printf("%s: get [%s]... [ok]\n", n, pkguri)
	}
}

// EOF
