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

	cfg, err := g_ctx.LocalCfg()
	handle_err(err)

	srcdir := "src"
	if cfg.HasOption("hwaf-cfg", "cmtpkgs") {
		srcdir, err = cfg.String("hwaf-cfg", "cmtpkgs")
		handle_err(err)
	}

	pkg := pkgname
	if !path_exists(pkg) {
		pkg = filepath.Join(srcdir, pkgname)
		if !path_exists(pkg) {
			err = fmt.Errorf("%s: no such package [%s]", n, pkgname)
			handle_err(err)
		}
	}

	if !g_ctx.PkgDb.HasPkg(pkg) {
		err = fmt.Errorf("%s: no such package [%s] in db", n, pkg)
		handle_err(err)
	}

	vcspkg, err := g_ctx.PkgDb.GetPkg(pkg)
	handle_err(err)

	switch vcspkg.Type {

	case "git":
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

	case "svn":
		if path_exists(vcspkg.Path) {
			err = os.RemoveAll(vcspkg.Path)
			handle_err(err)
			path := vcspkg.Path
			// clean-up dir if empty...
			for {
				path = filepath.Dir(path)
				if path == srcdir {
					break
				}
				content, err := filepath.Glob(filepath.Join(path, "*"))
				handle_err(err)
				if len(content) > 0 {
					break
				}
				err = os.RemoveAll(path)
				handle_err(err)
			}
		}

	default:
		err = fmt.Errorf("%s: VCS of type [%s] is not handled", n, vcspkg.Type)
		handle_err(err)
	}

	if !quiet {
		fmt.Printf("%s: remove package [%s]... [ok]\n", n, pkgname)
	}
}

// EOF
