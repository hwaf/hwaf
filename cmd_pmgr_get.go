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

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
)

func hwaf_make_cmd_pmgr_get() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_pmgr_get,
		UsageLine: "get [options] <pkguri>",
		Short:     "download and install a package/project",
		Long: `
get downloads and installs a package or project from a URI.

ex:
 $ hwaf pmgr get cern.ch/mana-fwk/mana-latest
 $ hwaf pmgr get -o /opt cern.ch/mana-fwk/mana-latest
`,
		Flag: *flag.NewFlagSet("hwaf-pmgr-get", flag.ExitOnError),
	}
	cmd.Flag.Bool("v", false, "enable verbose output")
	cmd.Flag.String("o", "", "directory where to install the package")
	return cmd
}

func hwaf_run_cmd_pmgr_get(cmd *commander.Command, args []string) error {
	var err error
	n := "hwaf-pmgr-" + cmd.Name()
	verbose := cmd.Flag.Lookup("v").Value.Get().(bool)

	pkguri := ""
	switch len(args) {
	case 1:
		pkguri = args[0]
	default:
		return fmt.Errorf("%s: you need to give a package URI to install", n)
	}

	pkguri = strings.Replace(pkguri, "http://", "", 1)
	pkguri = strings.Replace(pkguri, "https://", "", 1)

	if verbose {
		fmt.Printf("%s: get [%s]...\n", n, pkguri)
	}

	//manifest_url := path.Join(pkguri, "MANIFEST")

	if verbose {
		fmt.Printf("%s: get [%s]... [ok]\n", n, pkguri)
	}

	return err
}

// EOF
