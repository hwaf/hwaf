package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"

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
 $ hwaf pkg co -b=rel/mana git://github.com/mana-fwk/mana-core-athenakernel Control/AthenaKernel
 $ hwaf pkg co -b=AthenaKernel-00-00-01 svn+ssh://svn.cern.ch/reps/atlasoff/Control/AthenaKernel Control/AthenaKernel
`,
		Flag: *flag.NewFlagSet("hwaf-pkg-co", flag.ExitOnError),
	}
	cmd.Flag.Bool("q", true, "only print error and warning messages, all other output will be suppressed")
	cmd.Flag.String("b", "", "branch to checkout (default=master)")

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
	bname := cmd.Flag.Lookup("b").Value.Get().(string)

	if !quiet {
		fmt.Printf("%s: checkout package [%s]...\n", n, pkguri)
	}

	cfg := load_local_cfg()
	pkgdir := "src"
	if cfg.HasOption("hwaf-cfg", "cmtpkgs") {
		pkgdir, err = cfg.String("hwaf-cfg", "cmtpkgs")
		handle_err(err)
	}

	if strings.HasPrefix(pkguri, "svn+ssh:/") {
		fmt.Printf("%s: svn repo. doing staging...\n", n)
		staging := filepath.Join(".git", "hwaf-svn-staging")
		if !path_exists(staging) {
			err = os.MkdirAll(staging, 0700)
			handle_err(err)
		}
		_ = os.RemoveAll(filepath.Join(staging, pkgname))
		err = os.MkdirAll(filepath.Join(staging, pkgname), 0700)
		handle_err(err)
		git := exec.Command(
			"hwaf", "git", "svn-clone", "-verbose", "-revision=1", pkguri,
		)
		git.Dir = filepath.Join(staging, pkgname)
		err = git.Run()
		handle_err(err)

		pkguri, err = filepath.Abs(filepath.Join(staging, pkgname))
		handle_err(err)
		fmt.Printf("%s: svn repo. doing staging... [ok]\n", n)
	}
	git := exec.Command(
		"git", "submodule", "add",
		pkguri, filepath.Join(pkgdir, pkgname),
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

	if bname != "" {
		git = exec.Command(
			"git", "checkout", bname,
		)
		git.Dir = filepath.Join(pkgdir, pkgname)
		err = git.Run()
		handle_err(err)
	}

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
