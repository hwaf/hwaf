package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
	//gocfg "github.com/sbinet/go-config/config"
	_ "github.com/mana-fwk/git-tools/utils"
)

func hwaf_make_cmd_pkg_rm() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_pkg_rm,
		UsageLine: "rm [options] <local-pkg-name>",
		Short:     "remove a package from the current workarea",
		Long: `
rm removes a package from the current workarea.

ex:
 $ hwaf pkg rm ./src/foo/pkg
 $ hwaf pkg rm Control/AthenaKernel
`,
		Flag: *flag.NewFlagSet("hwaf-pkg-rm", flag.ExitOnError),
	}
	cmd.Flag.Bool("q", true, "only print error and warning messages, all other output will be suppressed")

	return cmd
}

func hwaf_run_cmd_pkg_rm(cmd *commander.Command, args []string) {
	var err error
	n := "hwaf-pkg-" + cmd.Name()
	pkgname := ""
	switch len(args) {
	case 1:
		pkgname = args[0]
	default:
		err = fmt.Errorf("%s: you need to give a package name to remove", n)
		handle_err(err)
	}

	pkgname = os.ExpandEnv(pkgname)
	pkgname = filepath.Clean(pkgname)

	quiet := cmd.Flag.Lookup("q").Value.Get().(bool)

	if !quiet {
		fmt.Printf("%s: remove package [%s]...\n", n, pkgname)
	}

	cfg := load_local_cfg()
	srcdir := "src"
	if cfg.HasOption("hwaf-cfg", "cmtpkgs") {
		srcdir, err = cfg.String("hwaf-cfg", "cmtpkgs")
		handle_err(err)
	}

	pkg := pkgname
	if !path_exists(pkg) {
		pkg = filepath.Join(srcdir, pkgname)
		if !path_exists(pkg) {
			err = fmt.Errorf("no such package [%s]", pkgname)
			handle_err(err)
		}
	}

	rmcmd := []string{"rm-submodule"}
	if !quiet {
		rmcmd = append(rmcmd, "--verbose")
	}
	rmcmd = append(rmcmd, pkg)
	git := exec.Command("git", rmcmd...)
	if !quiet {
		git.Stdin = os.Stdin
		git.Stdout = os.Stdout
		git.Stderr = os.Stderr
	}
	err = git.Run()
	handle_err(err)

	if !quiet {
		fmt.Printf("%s: remove package [%s]... [ok]\n", n, pkgname)
	}
}

// EOF
