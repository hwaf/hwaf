package main

import (
	"fmt"
	"io"
	"io/ioutil"
	"os"
	"os/exec"
	"path/filepath"
	"strings"

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
	cmd.Flag.String("name", "", "workarea/project name (default: directory-name)")
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
	proj_name := cmd.Flag.Lookup("name").Value.Get().(string)
	if proj_name == "" {
		proj_name = filepath.Base(dirname)
	}
	if proj_name == "." {
		pwd, err := os.Getwd()
		handle_err(err)
		proj_name = filepath.Base(pwd)
	}

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
		// first try the r/w url...
		git = exec.Command(
			"git", "clone", "git@github.com:mana-fwk/hep-waftools",
			hwaf_tools_dir,
		)
		if !quiet {
			git.Stdout = os.Stdout
			git.Stderr = os.Stderr
		}

		if git.Run() != nil {
			git := exec.Command(
				"git", "clone", "git://github.com/mana-fwk/hep-waftools",
				hwaf_tools_dir,
			)
			if !quiet {
				git.Stdout = os.Stdout
				git.Stderr = os.Stderr
			}
			err = git.Run()
			handle_err(err)
		}
	}
	if !path_exists(".hwaf") {
		err = os.MkdirAll(".hwaf", 0700)
		handle_err(err)
	}
	if path_exists(".hwaf/tools") {
		err = os.RemoveAll(".hwaf/tools")
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

	if !path_exists("wscript") {
		wscript_tmpl, err := os.Open(".hwaf/tools/hwaf-wscript")
		handle_err(err)
		defer wscript_tmpl.Close()

		wscript_b, err := ioutil.ReadAll(wscript_tmpl)
		handle_err(err)

		// replace 'hwaf-workarea' with workarea name
		wscript_s := strings.Replace(
			string(wscript_b),
			"APPNAME = 'hwaf-workarea'",
			fmt.Sprintf("APPNAME = '%s'", proj_name),
			-1)

		wscript, err := os.Create("wscript")
		handle_err(err)
		defer wscript.Close()

		_, err = io.WriteString(wscript, wscript_s)
		handle_err(err)
		handle_err(wscript.Sync())
		handle_err(wscript.Close())
	}

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

	// add a default .gitignore
	gitignore_tmpl, err := os.Open(".hwaf/tools/.gitignore")
	handle_err(err)
	defer gitignore_tmpl.Close()

	gitignore, err := os.Create(".gitignore")
	handle_err(err)
	defer gitignore.Close()

	_, err = io.Copy(gitignore, gitignore_tmpl)
	handle_err(err)
	handle_err(gitignore.Sync())
	handle_err(gitignore.Close())

	git = exec.Command("git", "add", ".gitignore")
	if !quiet {
		git.Stdout = os.Stdout
		git.Stderr = os.Stderr
	}
	err = git.Run()
	handle_err(err)

	// check whether we need to commit
	err = exec.Command("git", "diff", "--exit-code", "--quiet", "HEAD").Run()
	if err != nil {
		// commit
		if !quiet {
			fmt.Printf("%s: commit workarea...\n", n)
		}
		git = exec.Command(
			"git", "commit", "-m",
			fmt.Sprintf("init hwaf project [%s]", proj_name),
			)
		if !quiet {
			git.Stdout = os.Stdout
			git.Stderr = os.Stderr
		}
		err = git.Run()
		handle_err(err)
	}

	if !quiet {
		fmt.Printf("%s: creating workarea [%s]... [ok]\n", n, dirname)
	}
}

// EOF
