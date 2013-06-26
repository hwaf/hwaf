package main

import (
	"fmt"
	"io"
	"io/ioutil"
	"os"
	"os/exec"
	"os/user"
	"path/filepath"
	"strings"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
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
	cmd.Flag.Bool("q", true, "only print error and warning messages, all other output will be suppressed")
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
	proj_name := dirname
	if proj_name == "." {
		pwd, err := os.Getwd()
		handle_err(err)
		proj_name = filepath.Base(pwd)
	} else {
		proj_name = filepath.Base(dirname)
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
	hwaf_tools_dir := ""
	if g_ctx.Root != "" {
		hwaf_tools_dir = filepath.Join(g_ctx.Root, "share", "hwaf", "tools")
	} else {
		hwaf_tools_dir = filepath.Join("${HOME}", ".config", "hwaf", "tools")
	}
	hwaf_tools_dir = os.ExpandEnv(hwaf_tools_dir)
	if !path_exists(hwaf_tools_dir) {
		// first try the r/w url...
		git = exec.Command(
			"git", "clone", "git@github.com:hwaf/hep-waftools",
			hwaf_tools_dir,
		)
		if !quiet {
			git.Stdout = os.Stdout
			git.Stderr = os.Stderr
		}

		if git.Run() != nil {
			git := exec.Command(
				"git", "clone", "git://github.com/hwaf/hep-waftools",
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

	git = exec.Command("git", "add", "-f", ".hwaf/tools")
	if !quiet {
		git.Stdout = os.Stdout
		git.Stderr = os.Stderr
	}
	err = git.Run()
	handle_err(err)

	// add waf-bin
	{
		if !quiet {
			fmt.Printf("%s: add .hwaf/bin...\n", n)
		}
		hwaf_bin_dir := ""
		if g_ctx.Root != "" {
			hwaf_bin_dir = filepath.Join(g_ctx.Root, "bin")
		} else {
			hwaf_bin_dir = filepath.Join("${HOME}", ".config", "hwaf", "bin")
		}
		hwaf_bin_dir = os.ExpandEnv(hwaf_bin_dir)
		if !path_exists(hwaf_bin_dir) {
			err = fmt.Errorf("no such hwaf-bin dir [%s]", hwaf_bin_dir)
			handle_err(err)
		}
		src_waf, err := os.Open(filepath.Join(hwaf_bin_dir, "waf"))
		handle_err(err)
		defer src_waf.Close()

		if !path_exists(".hwaf/bin") {
			err = os.MkdirAll(".hwaf/bin", 0700)
			handle_err(err)
		}

		waf_bin, err := os.Create(filepath.Join(".hwaf", "bin", "waf"))
		handle_err(err)
		defer waf_bin.Close()

		err = waf_bin.Chmod(0755)
		handle_err(err)

		_, err = io.Copy(waf_bin, src_waf)
		handle_err(err)

		err = waf_bin.Sync()
		handle_err(err)
	}

	// add pkgdb
	err = ioutil.WriteFile(
		filepath.Join(".hwaf", "pkgdb.json"),
		[]byte("{}\n"),
		0755,
	)
	handle_err(err)
	git = exec.Command("git", "add", "-f", filepath.Join(".hwaf", "pkgdb.json"))
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

	// create 'src' directory
	if !path_exists("src") {
		err = os.MkdirAll("src", 0700)
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
		// check if we have enough informations about the user name
		git = exec.Command("git", "config", "--global", "user.name")
		if git.Run() != nil {
			usr, err2 := user.Current()
			usrname := "nobody"
			if err2 == nil {
				if usr.Name != "" {
					usrname = usr.Name
				} else {
					usrname = usr.Username
				}
			}
			g_ctx.Warn("git wasn't properly configured: missing 'user.name' info => setting it to %q\n", usrname)
			git = exec.Command("git", "config", "user.name", usrname)
			err = git.Run()
			handle_err(err)
		}

		// check if we have enough informations about the user email
		git = exec.Command("git", "config", "--global", "user.email")
		if git.Run() != nil {
			usr, err2 := user.Current()
			usrmail := usr.Username
			if err2 != nil {
				usrmail = "nobody"
			}
			hostname, err2 := os.Hostname()
			if err2 != nil {
				hostname = "localhost.localdomain"
			}
			usrmail = usrmail + "@" + hostname
			g_ctx.Warn("git wasn't properly configured: missing 'user.email' info => setting it to %q\n", usrmail)
			git = exec.Command("git", "config", "user.email", usrmail)
			err = git.Run()
			handle_err(err)
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
