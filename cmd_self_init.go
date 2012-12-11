package main

import (
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"

	"github.com/sbinet/go-commander"
	"github.com/sbinet/go-flag"
)

func hwaf_make_cmd_self_init() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_self_init,
		UsageLine: "self-init [options] <workarea>",
		Short:     "initialize hwaf proper",
		Long: `
self-init initializes hwaf internal files.

ex:
 $ hwaf self-init
`,
		Flag: *flag.NewFlagSet("hwaf-self-init", flag.ExitOnError),
	}
	cmd.Flag.Bool("q", false, "only print error and warning messages, all other output will be suppressed")

	return cmd
}

func hwaf_run_cmd_self_init(cmd *commander.Command, args []string) {
	var err error
	n := "hwaf-" + cmd.Name()

	switch len(args) {
	case 0:
		// ok
	default:
		err = fmt.Errorf("%s: does NOT take any argument", n)
		handle_err(err)
	}

	quiet := cmd.Flag.Lookup("q").Value.Get().(bool)

	if !quiet {
		fmt.Printf("%s: self-init...\n", n)
	}

	top := hwaf_root()
	if !path_exists(top) {
		err = os.MkdirAll(top, 0700)
		handle_err(err)
	}

	// add hep-waftools cache
	hwaf_tools := filepath.Join(top, "tools")
	if path_exists(hwaf_tools) {
		err = os.RemoveAll(hwaf_tools)
		handle_err(err)
	}
	git := exec.Command(
		"git", "clone", "git://github.com/mana-fwk/hep-waftools",
		hwaf_tools,
	)
	if !quiet {
		git.Stdout = os.Stdout
		git.Stderr = os.Stderr
	}
	err = git.Run()
	handle_err(err)

	// add bin dir
	bin := filepath.Join(top, "bin")
	if !path_exists(bin) {
		err = os.MkdirAll(bin, 0700)
		handle_err(err)
	}
	
	// add waf-bin
	waf_fname := filepath.Join(bin, "waf")
	if path_exists(waf_fname) {
		err = os.Remove(waf_fname)
		handle_err(err)
	}
	waf, err := os.Create(waf_fname)
	handle_err(err)
	defer waf.Close()

	resp, err := http.Get("https://github.com/mana-fwk/hwaf/raw/master/waf")
	handle_err(err)
	defer resp.Body.Close()
	_, err = io.Copy(waf, resp.Body)
	handle_err(err)

	if !quiet {
		fmt.Printf("%s: self-init... [ok]\n", n)
	}
}

// EOF
