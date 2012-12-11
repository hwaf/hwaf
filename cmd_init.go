package main

import (
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"

	"github.com/sbinet/go-commander"
	"github.com/sbinet/go-flag"
)

func hwaf_make_cmd_init() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_init,
		UsageLine: "init [options] <workarea>",
		Short:     "initialize a new workarea",
		Long: `
init initializes a new workarea.

ex:
 $ hwaf init
 $ hwaf init .
 $ hwaf init my-work-area
`,
		Flag: *flag.NewFlagSet("hwaf-init", flag.ExitOnError),
	}
	cmd.Flag.Bool("q", false, "only print error and warning messages, all other output will be suppressed")

	return cmd
}

func hwaf_run_cmd_init(cmd *commander.Command, args []string) {
	var err error
	n := "hwaf-" + cmd.Name()
	dirname := ""

	switch len(args) {
	case 0:
		dirname = "."
	case 1:
		dirname = args[0]
	default:
		err = fmt.Errorf("%s: you need to give a directory name", n)
		handle_err(err)
	}

	dirname = os.ExpandEnv(dirname)
	dirname = filepath.Clean(dirname)

	quiet := cmd.Flag.Lookup("q").Value.Get().(bool)

	if !quiet {
		fmt.Printf("%s: creating workarea [%s]...\n", n, dirname)
	}

	if !path_exists(dirname) {
		err = os.MkdirAll(dirname, 0700)
		handle_err(err)
	}

	pwd, err := os.Getwd()
	handle_err(err)
	defer os.Chdir(pwd)

	err = os.Chdir(dirname)
	handle_err(err)

	// init a git repository in dirname
	if !quiet {
		fmt.Printf("%s: initialize git workarea repository...\n", n)
	}
	git := exec.Command("git", "init", ".")
	if !quiet {
		git.Stdout = os.Stdout
		git.Stderr = os.Stderr
	}
	err = git.Run()
	handle_err(err)

	// add hep-waf-tools
	if !quiet {
		fmt.Printf("%s: add .hwaf/tools...\n", n)
	}
	hwaf_tools_dir := filepath.Join("${HOME}", ".config", "hwaf", "tools")
	hwaf_tools_dir = os.ExpandEnv(hwaf_tools_dir)
	if !path_exists(hwaf_tools_dir) {
		git = exec.Command(
			"git", "clone",
			"git://github.com/mana-fwk/hep-waftools",
			hwaf_tools_dir,
		)
		if !quiet {
			git.Stdout = os.Stdout
			git.Stderr = os.Stderr
		}
		err = git.Run()
		handle_err(err)
	}
	if !path_exists(".hwaf") {
		err = os.MkdirAll(".hwaf", 0700)
		handle_err(err)
	}
	err = os.Symlink(hwaf_tools_dir, ".hwaf/tools")
	handle_err(err)

	git = exec.Command("git", "add", ".hwaf/tools")
	if !quiet {
		git.Stdout = os.Stdout
		git.Stderr = os.Stderr
	}
	err = git.Run()
	handle_err(err)

	// add template wscript
	if !quiet {
		fmt.Printf("%s: add top-level wscript...\n", n)
	}

	wscript, err := os.Create("wscript")
	handle_err(err)
	defer wscript.Close()

	wscript_tmpl, err := os.Open(".hwaf/tools/hwaf-wscript")
	handle_err(err)
	defer wscript_tmpl.Close()

	_, err = io.Copy(wscript, wscript_tmpl)
	handle_err(err)
	handle_err(wscript.Sync())
	handle_err(wscript.Close())

	git = exec.Command("git", "add", "wscript")
	if !quiet {
		git.Stdout = os.Stdout
		git.Stderr = os.Stderr
	}
	err = git.Run()
	handle_err(err)

	// create 'pkg' directory
	if !path_exists("pkg") {
		err = os.MkdirAll("pkg", 0700)
		handle_err(err)
	}

	// commit
	if !quiet {
		fmt.Printf("%s: commit workarea...\n", n)
	}
	git = exec.Command("git", "commit", "-m", `"init hwaf workarea"`)
	if !quiet {
		git.Stdout = os.Stdout
		git.Stderr = os.Stderr
	}
	err = git.Run()
	handle_err(err)

	if !quiet {
		fmt.Printf("%s: creating workarea [%s]... [ok]\n", n, dirname)
	}
}

// EOF
