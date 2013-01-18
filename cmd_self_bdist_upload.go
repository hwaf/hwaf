package main

import (
	"fmt"
	"os"
	"os/exec"
	"runtime"
	"time"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
)

func hwaf_make_cmd_self_bdist_upload() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_self_bdist_upload,
		UsageLine: "bdist-upload [options] [filename.tar.gz]",
		Short:     "upload hwaf binary distribution to cern.ch/mana-fwk",
		Long: `
bdist-upload uploads a hwaf binary distribution to http://cern.ch/mana-fwk.

ex:
 $ hwaf self bdist-upload
 $ hwaf self bdist-upload hwaf-20130101-linux-amd64.tar.gz
`,
		Flag: *flag.NewFlagSet("hwaf-self-bdist-upload", flag.ExitOnError),
	}
	cmd.Flag.Bool("q", true, "only print error and warning messages, all other output will be suppressed")
	return cmd
}

func hwaf_run_cmd_self_bdist_upload(cmd *commander.Command, args []string) {
	var err error
	n := "hwaf-self-" + cmd.Name()

	fname := ""
	switch len(args) {
	case 0:
		vers := time.Now().Format("20060102")
		arch := fmt.Sprintf("%s-%s", runtime.GOOS, runtime.GOARCH)
		fname = fmt.Sprintf("hwaf-%s-%s.tar.gz", vers, arch)
	case 1:
		fname = args[0]
	default:
		err = fmt.Errorf("%s: takes a path to a file to upload", n)
		handle_err(err)
	}

	quiet := cmd.Flag.Lookup("q").Value.Get().(bool)

	if !quiet {
		fmt.Printf("%s [%s]...\n", n, fname)
	}

	if !path_exists(fname) {
		fname = os.ExpandEnv(fname)
		if !path_exists(fname) {
			err = fmt.Errorf("no such file [%s]", fname)
			handle_err(err)
		}
	}

	dst_dir := "binet@lxplus.cern.ch:~/dev/repos/mana-fwk/www/downloads/tar"
	dst := fmt.Sprintf("%s/%s", dst_dir, fname)
	scp := exec.Command("scp", fname, dst)
	scp.Stdin = os.Stdin
	scp.Stdout = os.Stdout
	scp.Stderr = os.Stderr
	err = scp.Run()
	handle_err(err)

	if !quiet {
		fmt.Printf("%s [%s]... [ok]\n", n, fname)
	}
}

// EOF
