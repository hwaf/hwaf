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
		UsageLine: "rm [options] <local-pkg-name> [<pkg2> [...]]",
		Short:     "remove a package from the current workarea",
		Long: `
rm removes a package from the current workarea.

ex:
 $ hwaf pkg rm ./src/foo/pkg
 $ hwaf pkg rm Control/AthenaKernel
 $ hwaf pkg rm Control/AthenaKernel Control/AthenaServices
`,
		Flag: *flag.NewFlagSet("hwaf-pkg-rm", flag.ExitOnError),
	}
	cmd.Flag.Bool("q", true, "only print error and warning messages, all other output will be suppressed")

	return cmd
}

func hwaf_run_cmd_pkg_rm(cmd *commander.Command, args []string) {
	var err error
	n := "hwaf-pkg-" + cmd.Name()
	switch len(args) {
	case 0:
		err = fmt.Errorf("%s: you need to give (at least) one package name to remove", n)
		handle_err(err)
	}

	quiet := cmd.Flag.Lookup("q").Value.Get().(bool)

	cfg, err := g_ctx.LocalCfg()
	handle_err(err)

	srcdir := "src"
	if cfg.HasOption("hwaf-cfg", "cmtpkgs") {
		srcdir, err = cfg.String("hwaf-cfg", "cmtpkgs")
		handle_err(err)
	}

	do_rm := func(pkgname string) error {
		var err error

		pkgname = os.ExpandEnv(pkgname)
		pkgname = filepath.Clean(pkgname)
		if !quiet {
			fmt.Printf("%s: remove package [%s]...\n", n, pkgname)
		}

		pkg := pkgname
		if !g_ctx.PkgDb.HasPkg(pkg) {
			pkg = filepath.Join(srcdir, pkgname)
		}
		if !g_ctx.PkgDb.HasPkg(pkg) {
			return fmt.Errorf("%s: no such package [%s] in db", n, pkg)
		}

		// people may have already removed it via a simple 'rm -rf foo'...
		//
		// if !path_exists(pkg) {
		// 	pkg = filepath.Join(srcdir, pkgname)
		// 	if !path_exists(pkg) {
		// 		err = fmt.Errorf("%s: no such package [%s]", n, pkgname)
		// 		handle_err(err)
		// 	}
		// }

		if !g_ctx.PkgDb.HasPkg(pkg) {
			return fmt.Errorf("%s: no such package [%s] in db", n, pkg)
		}

		vcspkg, err := g_ctx.PkgDb.GetPkg(pkg)
		if err != nil {
			return err
		}

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
			if err != nil {
				return err
			}

		case "svn":
			if path_exists(vcspkg.Path) {
				err = os.RemoveAll(vcspkg.Path)
				if err != nil {
					return err
				}
				path := vcspkg.Path
				// clean-up dir if empty...
				for {
					path = filepath.Dir(path)
					if path == srcdir {
						break
					}
					content, err := filepath.Glob(filepath.Join(path, "*"))
					if err != nil {
						return err
					}
					if len(content) > 0 {
						break
					}
					err = os.RemoveAll(path)
					if err != nil {
						return err
					}
				}
			}

		case "local":
			// local packages are tracked from workarea-git-repo
			git := exec.Command("git", "rm", "-r", vcspkg.Path)
			if !quiet {
				git.Stdin = os.Stdin
				git.Stdout = os.Stdout
				git.Stderr = os.Stderr
			}
			err = git.Run()
			if err != nil {
				return err
			}
			git = exec.Command(
				"git", "commit", "-m",
				fmt.Sprintf("removed local package [%s]", vcspkg.Path),
			)
			err = git.Run()
			if err != nil {
				return err
			}
			if path_exists(vcspkg.Path) {
				err = os.RemoveAll(vcspkg.Path)
				if err != nil {
					return err
				}
				path := vcspkg.Path
				// clean-up dir if empty...
				for {
					path = filepath.Dir(path)
					if path == srcdir {
						break
					}
					content, err := filepath.Glob(filepath.Join(path, "*"))
					if err != nil {
						return err
					}
					if len(content) > 0 {
						break
					}
					err = os.RemoveAll(path)
					if err != nil {
						return err
					}
				}
			}

		default:
			return fmt.Errorf("%s: VCS of type [%s] is not handled", n, vcspkg.Type)
		}

		err = g_ctx.PkgDb.Remove(pkg)
		if err != nil {
			return err
		}

		if !quiet {
			fmt.Printf("%s: remove package [%s]... [ok]\n", n, pkgname)
		}
		return nil
	}

	for _, pkgname := range args {
		err := do_rm(pkgname)
		handle_err(err)
	}
}

// EOF
