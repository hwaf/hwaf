package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
)

func hwaf_make_cmd_git_rm_submodule() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_git_rm_submodule,
		UsageLine: "rm-submodule [options] <directory>",
		Short:     "remove a submodule",
		Long: `
rm-submodule removes a submodule from a GIT repository.

ex:
 $ hwaf git rm-submodule Control/AthenaCommon
 $ hwaf git rm-submodule src/Control/AthenaCommon
 $ hwaf git rm-submodule -no-commit src/Control/AthenaCommon
`,
		Flag: *flag.NewFlagSet("hwaf-git-rm-submodule", flag.ExitOnError),
	}
	cmd.Flag.Bool("no-commit", true, "do not commit the result")
	return cmd
}

func hwaf_run_cmd_git_rm_submodule(cmd *commander.Command, args []string) {
	var err error
	n := "hwaf-" + cmd.Name()

	pkgdir := ""
	pkgname := ""
	switch len(args) {
	case 1:
		pkgdir = args[0]
		pkgname = args[0]
	default:
		err = fmt.Errorf("%s: needs a submodule name to remove", n)
		handle_err(err)
	}

	nocommit := cmd.Flag.Lookup("no-commit").Value.Get().(bool)

	cmtpkgdir := "src"

	if !path_exists(pkgdir) {
		cfg, err := g_ctx.LocalCfg()
		handle_err(err)
		if cfg.HasOption("hwaf-cfg", "cmtpkgs") {
			cmtpkgdir, err = cfg.String("hwaf-cfg", "cmtpkgs")
			handle_err(err)
		}
		if path_exists(filepath.Join(cmtpkgdir, pkgdir)) {
			pkgdir = filepath.Join(cmtpkgdir, pkgdir)
		}
	}

	pkgdir = os.ExpandEnv(pkgdir)
	pkgdir = filepath.Clean(pkgdir)

	if !path_exists(pkgdir) {
		err = fmt.Errorf("no such directory [%s]", pkgdir)
		handle_err(err)
	}

	if !nocommit {
		git := exec.Command("git", "add", ".gitmodules")
		err = git.Run()
		handle_err(err)

		git = exec.Command(
			"git", "commit", "-m",
			fmt.Sprintf("removed submodule [%s]", pkgname),
		)
		err = git.Run()
		handle_err(err)
	}

	handle_err(err)
}

// EOF
