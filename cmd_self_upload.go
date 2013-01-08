package main

import (
	"fmt"
	"os"
	"os/exec"
	"runtime"

	"github.com/sbinet/go-commander"
	"github.com/sbinet/go-flag"
)

func hwaf_make_cmd_self_upload() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_self_upload,
		UsageLine: "upload",
		Short:     "upload hwaf to cern.ch/mana-fwk",
		Long: `
upload uploads hwaf to http://cern.ch/mana-fwk.

ex:
 $ hwaf self upload
`,
		Flag: *flag.NewFlagSet("hwaf-self-upload", flag.ExitOnError),
	}
	cmd.Flag.Bool("q", false, "only print error and warning messages, all other output will be suppressed")

	return cmd
}

func hwaf_run_cmd_self_upload(cmd *commander.Command, args []string) {
	var err error
	n := "hwaf-self-" + cmd.Name()

	switch len(args) {
	case 0:
		// ok
	default:
		err = fmt.Errorf("%s: does NOT take any argument", n)
		handle_err(err)
	}

	quiet := cmd.Flag.Lookup("q").Value.Get().(bool)

	if !quiet {
		fmt.Printf("%s: self-upload...\n", n)
	}

	old, err := exec.LookPath(os.Args[0])
	handle_err(err)
	dst_dir := "binet@lxplus.cern.ch:~/dev/repos/mana-fwk/www/downloads/bin"
	dst := fmt.Sprintf("%s/hwaf-%s-%s", dst_dir, runtime.GOOS, runtime.GOARCH)
	scp := exec.Command("scp", old, dst)
	scp.Stdin = os.Stdin
	scp.Stdout = os.Stdout
	scp.Stderr = os.Stderr
	err = scp.Run()
	handle_err(err)

	if !quiet {
		fmt.Printf("%s: self-upload... [ok]\n", n)
	}
}

// EOF
