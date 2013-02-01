package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
)

func hwaf_make_cmd_cmt_cnv() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_cmt_cnv,
		UsageLine: "cmt-cnv [options] <req-file>",
		Short:     "convert a CMT req-file into a hwaf script",
		Long: `
cmt-cnv converts a CMT req-file into a hwaf script.

ex:
 $ hwaf cmt-cnv ./cmt/requirements
`,
		Flag:        *flag.NewFlagSet("hwaf-cmt-cnv", flag.ExitOnError),
	//CustomFlags: true,
	}
	cmd.Flag.Bool("q", true, "only print error and warning messages, all other output will be suppressed")
	return cmd
}

func hwaf_run_cmd_cmt_cnv(cmd *commander.Command, args []string) {
	var err error
	n := "hwaf-" + cmd.Name()

	reqfile := ""
	switch len(args) {
	case 1:
		reqfile = args[0]
	default:
		err = fmt.Errorf("%s: you need to give a cmt/requirements file to convert", n)
		handle_err(err)
	}

	reqfile = os.ExpandEnv(reqfile)
	reqfile = filepath.Clean(reqfile)

	quiet := cmd.Flag.Lookup("q").Value.Get().(bool)

	if !quiet {
		fmt.Printf("%s: converting [%s]...\n", n, reqfile)
	}

	subargs := append([]string{}, args...)
	sub := exec.Command("cmt", subargs...)
	sub.Stdin = os.Stdin
	sub.Stdout = os.Stdout
	sub.Stderr = os.Stderr
	err = sub.Run()
	handle_err(err)

	if !quiet {
		fmt.Printf("%s: converting [%s]... [ok]\n", n, reqfile)
	}
}

// EOF
