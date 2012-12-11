package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"

	"github.com/sbinet/go-commander"
	"github.com/sbinet/go-flag"
	//gocfg "github.com/sbinet/go-config/config"
)

func hwaf_make_cmd_checkout() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_checkout,
		UsageLine: "co [options] <pkg-uri> [<local-pkg-name>]",
		Short:     "add a package to the current workarea",
		Long: `
co adds a package to the current workarea.

ex:
 $ hwaf co /foo/pkg
 $ hwaf co Control/AthenaKernel
 $ hwaf co git://github.com/mana-fwk/mana-core-athenakernel
 $ hwaf co git://github.com/mana-fwk/mana-core-athenakernel Control/AthenaKernel
`,
		Flag: *flag.NewFlagSet("hwaf-checkout", flag.ExitOnError),
	}
	cmd.Flag.Bool("q", false, "only print error and warning messages, all other output will be suppressed")

	return cmd
}

func hwaf_run_cmd_checkout(cmd *commander.Command, args []string) {
	var err error
	n := "hwaf-" + cmd.Name()
	pkguri := ""
	pkgname := ""
	switch len(args) {
	case 1:
		pkguri = args[0]
		pkgname = filepath.Base(args[0])
	case 2:
		pkguri = args[0]
		pkgname = args[1]
	default:
		err = fmt.Errorf("%s: you need to give a package URL", n)
		handle_err(err)
	}

	pkguri = os.ExpandEnv(pkguri)
	//pkguri = filepath.Clean(pkguri)

	pkgname = os.ExpandEnv(pkgname)
	pkgname = filepath.Clean(pkgname)

	quiet := cmd.Flag.Lookup("q").Value.Get().(bool)

	if !quiet {
		fmt.Printf("%s: checkout package [%s]...\n", n, pkguri)
	}

	cfg := load_local_cfg()
	pkgdir := "pkg"
	if cfg.HasOption("hwaf-cfg", "cmtpkgs") {
		pkgdir, err = cfg.String("hwaf-cfg", "cmtpkgs")
		handle_err(err)
	}

	git := exec.Command("git", "submodule", "add",
		pkguri,
		filepath.Join(pkgdir, pkgname),
	)
	if !quiet {
		git.Stdout = os.Stdout
		git.Stderr = os.Stderr
	}
	err = git.Run()
	handle_err(err)

	git = exec.Command(
		"git", "submodule", "update",
		"--init", "--recursive",
	)
	if !quiet {
		git.Stdout = os.Stdout
		git.Stderr = os.Stderr
	}
	err = git.Run()
	handle_err(err)

	if !quiet {
		fmt.Printf("%s: checkout package [%s]... [ok]\n", n, pkguri)
	}
}

// EOF
