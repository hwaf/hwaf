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

func hwaf_run_cmd_init(cmd *commander.Command, args []string) error {
	var err error
	n := "hwaf-" + cmd.Name()
	dirname := ""

	switch len(args) {
	case 0:
		dirname = "."
	case 1:
		dirname = args[0]
	default:
		return fmt.Errorf("%s: you need to give a directory name", n)
	}

	dirname = os.ExpandEnv(dirname)
	dirname = filepath.Clean(dirname)

	verbose := cmd.Flag.Lookup("v").Value.Get().(bool)
	proj_name := dirname
	if proj_name == "." {
		pwd, err := os.Getwd()
		if err != nil {
			return err
		}
		proj_name = filepath.Base(pwd)
	} else {
		proj_name = filepath.Base(dirname)
	}

	if verbose {
		fmt.Printf("%s: creating workarea [%s]...\n", n, dirname)
	}

	if !path_exists(dirname) {
		err = os.MkdirAll(dirname, 0700)
		if err != nil {
			return err
		}
	}

	pwd, err := os.Getwd()
	if err != nil {
		return err
	}
	defer os.Chdir(pwd)

	err = os.Chdir(dirname)
	if err != nil {
		return err
	}

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
		if err != nil {
			return err
		}
	}

	hwaf_tools_dir = os.ExpandEnv(hwaf_tools_dir)
	if verbose {
		fmt.Printf("%s: using hwaf/tools from [%s]...\n", n, hwaf_tools_dir)
	}
	if !path_exists(hwaf_tools_dir) {
		return fmt.Errorf("no such directory [%s]", hwaf_tools_dir)
	}
	if !path_exists(".hwaf") {
		err = os.MkdirAll(".hwaf", 0700)
		if err != nil {
			return err
		}
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
			if err != nil {
				return err
			}
		}
		hwaf_bin_dir = os.ExpandEnv(hwaf_bin_dir)
		if verbose {
			fmt.Printf("%s: using hwaf-bin from [%s]...\n", n, hwaf_bin_dir)
		}
		if !path_exists(hwaf_bin_dir) {
			err = fmt.Errorf("no such hwaf-bin dir [%s]", hwaf_bin_dir)
			if err != nil {
				return err
			}
		}
		src_waf, err := os.Open(filepath.Join(hwaf_bin_dir, "waf"))
		if err != nil {
			return err
		}
		defer src_waf.Close()

		if !path_exists(".hwaf/bin") {
			err = os.MkdirAll(".hwaf/bin", 0700)
			if err != nil {
				return err
			}
		}

		waf_bin, err := os.Create(filepath.Join(".hwaf", "bin", "waf"))
		if err != nil {
			return err
		}
		defer waf_bin.Close()

		if runtime.GOOS != "windows" {
			err = waf_bin.Chmod(0755)
			if err != nil {
				return err
			}
		}

		_, err = io.Copy(waf_bin, src_waf)
		if err != nil {
			return err
		}

		err = waf_bin.Sync()
		if err != nil {
			return err
		}
	}

	// add pkgdb
	err = ioutil.WriteFile(
		filepath.Join(".hwaf", "pkgdb.json"),
		[]byte("{}\n"),
		0755,
	)
	if err != nil {
		return err
	}

	// add template wscript
	if verbose {
		fmt.Printf("%s: add top-level wscript...\n", n)
	}

	if !path_exists("wscript") {
		wscript_tmpl, err := os.Open(filepath.Join(hwaf_tools_dir, "hwaf-wscript"))
		if err != nil {
			return err
		}
		defer wscript_tmpl.Close()

		wscript_b, err := ioutil.ReadAll(wscript_tmpl)
		if err != nil {
			return err
		}

		// replace 'hwaf-workarea' with workarea name
		wscript_s := strings.Replace(
			string(wscript_b),
			"APPNAME = 'hwaf-workarea'",
			fmt.Sprintf("APPNAME = '%s'", proj_name),
			-1)

		wscript, err := os.Create("wscript")
		if err != nil {
			return err
		}
		defer wscript.Close()

		_, err = io.WriteString(wscript, wscript_s)
		if err != nil {
			return err
		}
		err = wscript.Sync()
		if err != nil {
			return err
		}
		err = wscript.Close()
		if err != nil {
			return err
		}
	}

	// create 'src' directory
	if !path_exists("src") {
		err = os.MkdirAll("src", 0700)
		if err != nil {
			return err
		}
	}

	if verbose {
		fmt.Printf("%s: creating workarea [%s]... [ok]\n", n, dirname)
	}

	return err
}

// EOF
