package main

import (
	"fmt"
	"io"
	"io/ioutil"
	"os"
	"path/filepath"
	"runtime"
	"strings"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
	"github.com/hwaf/gas"
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
	cmd.Flag.Bool("v", false, "enable verbose output")
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

	verbose := cmd.Flag.Lookup("v").Value.Get().(bool)
	proj_name := dirname
	if proj_name == "." {
		pwd, err := os.Getwd()
		handle_err(err)
		proj_name = filepath.Base(pwd)
	} else {
		proj_name = filepath.Base(dirname)
	}

	if verbose {
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

	// setup hep-waf-tools
	if verbose {
		fmt.Printf("%s: add .hwaf/tools...\n", n)
	}
	hwaf_tools_dir := ""
	switch g_ctx.Root {
	default:
		hwaf_tools_dir = filepath.Join(g_ctx.Root, "share", "hwaf", "tools")
	case "":
		hwaf_tools_dir, err = gas.Abs("github.com/hwaf/hwaf/py-hwaftools")
		handle_err(err)
	}

	hwaf_tools_dir = os.ExpandEnv(hwaf_tools_dir)
	if verbose {
		fmt.Printf("%s: using hwaf/tools from [%s]...\n", n, hwaf_tools_dir)
	}
	if !path_exists(hwaf_tools_dir) {
		err = fmt.Errorf("no such directory [%s]", hwaf_tools_dir)
		handle_err(err)
	}
	if !path_exists(".hwaf") {
		err = os.MkdirAll(".hwaf", 0700)
		handle_err(err)
	}

	// add waf-bin
	{
		if verbose {
			fmt.Printf("%s: add .hwaf/bin...\n", n)
		}
		hwaf_bin_dir := ""
		switch g_ctx.Root {
		default:
			hwaf_bin_dir = filepath.Join(g_ctx.Root, "bin")
		case "":
			hwaf_bin_dir, err = gas.Abs("github.com/hwaf/hwaf")
			handle_err(err)
		}
		hwaf_bin_dir = os.ExpandEnv(hwaf_bin_dir)
		if verbose {
			fmt.Printf("%s: using hwaf-bin from [%s]...\n", n, hwaf_bin_dir)
		}
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

		if runtime.GOOS != "windows" {
			err = waf_bin.Chmod(0755)
			handle_err(err)
		}

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

	// add template wscript
	if verbose {
		fmt.Printf("%s: add top-level wscript...\n", n)
	}

	if !path_exists("wscript") {
		wscript_tmpl, err := os.Open(filepath.Join(hwaf_tools_dir, "hwaf-wscript"))
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

	// create 'src' directory
	if !path_exists("src") {
		err = os.MkdirAll("src", 0700)
		handle_err(err)
	}

	if verbose {
		fmt.Printf("%s: creating workarea [%s]... [ok]\n", n, dirname)
	}
}

// EOF
