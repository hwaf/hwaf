package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
	//gocfg "github.com/sbinet/go-config/config"
)

func hwaf_make_cmd_pkg_add() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_pkg_add,
		UsageLine: "co [options] <pkg-uri> [<local-pkg-name>]",
		Short:     "add a package to the current workarea",
		Long: `
co adds a package to the current workarea.

ex:
 $ hwaf pkg co /foo/pkg
 $ hwaf pkg co Control/AthenaKernel
 $ hwaf pkg co git://github.com/mana-fwk/mana-core-athenakernel
 $ hwaf pkg co git://github.com/mana-fwk/mana-core-athenakernel Control/AthenaKernel
`,
		Flag: *flag.NewFlagSet("hwaf-pkg-co", flag.ExitOnError),
	}
	cmd.Flag.Bool("q", false, "only print error and warning messages, all other output will be suppressed")

	return cmd
}

func hwaf_run_cmd_pkg_add(cmd *commander.Command, args []string) {
	var err error
	n := "hwaf-pkg-" + cmd.Name()
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
	pkgdir := "src"
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

	git = exec.Command(
		"git", "commit", "-m",
		fmt.Sprintf("adding package [%s]", pkgname),
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
