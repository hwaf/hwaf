package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"

	"github.com/sbinet/go-commander"
	"github.com/sbinet/go-flag"
	//gocfg "github.com/sbinet/go-config/config"
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
	cmd.Flag.Bool("q", false, "only print error and warning messages, all other output will be suppressed")

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

	// make sure we get correct collated messages
	err = os.Setenv("LC_MESSAGES", "C")
	handle_err(err)

	// check the directory we have been given is a valid submodule
	git := exec.Command(
		"git", "ls-files", "--error-unmatch",
		"--stage",
		"--",
		pkg)
	out, err := git.Output()
	handle_err(err)
	if string(out) == "" {
		err = fmt.Errorf("[%s] is not a valid submodule", pkgname)
		handle_err(err)
	}

	// get the full path of the submodule
	git = exec.Command("git", "ls-files", "--full-name", pkg)
	out, err = git.Output()
	handle_err(err)
	pkg = strings.Trim(string(out), " \n\r")
	
	// get toplevel directory
	git = exec.Command("git", "rev-parse", "--show-toplevel")
	out, err = git.Output()
	handle_err(err)
	root := strings.Trim(string(out), " \n\r")
	err = os.Chdir(root)
	handle_err(err)

	err = os.Chdir(pkg)
	handle_err(err)

	// FIXME
	// for _,tst := range []string{"check-clean", "check-unpushed", "check-non-tracking"} {
	// 	git = exec.Command("git", tst)
	// 	if !quiet {
	// 		git.Stdin = os.Stdin
	// 		git.Stdout = os.Stdout
	// 		git.Stderr = os.Stderr
	// 	}
	// 	err = git.Run()
	// 	handle_err(err)
	// }

	// find the real git-dir
	git = exec.Command("git", "rev-parse", "--git-dir")
	out, err = git.Output()
	handle_err(err)
	gitdir := string(out)

	err = os.Chdir(root)
	handle_err(err)

	// ok, start removing now...

	// get submodule url
	git = exec.Command(
		"git", "config", "--get",
		fmt.Sprintf("submodule.%s.url", pkg),
		)
	out, err = git.Output()
	url := strings.Trim(string(out), " \r\n")
	if err != nil {
		url = "unknown"
	}

	// remove config entries
	exec.Command("git", "config", "-f", ".gitmodules",
		"--remove-section",
		fmt.Sprintf("submodule.%s", pkg),
		).Run()
	exec.Command("git", "config", "--remove-section",
		fmt.Sprintf("submodule.%s", pkg),
		).Run()
	git = exec.Command("git", "rm", "--cached", pkg)
	if !quiet {
		git.Stdin = os.Stdin
		git.Stdout = os.Stdout
		git.Stderr = os.Stderr
	}
	err = git.Run()
	handle_err(err)

	err = os.RemoveAll(pkg)
	handle_err(err)

	err = os.RemoveAll(gitdir)
	handle_err(err)

	// commit changes
	git = exec.Command("git", "add", ".gitmodules")
	if !quiet {
		git.Stdin = os.Stdin
		git.Stdout = os.Stdout
		git.Stderr = os.Stderr
	}
	err = git.Run()
	handle_err(err)

	git = exec.Command("git", "commit", "-m",
		fmt.Sprintf("removed package [%s] (url: %s)", pkgname, url),
		)
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
