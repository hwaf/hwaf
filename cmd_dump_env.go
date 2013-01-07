package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	// "path/filepath"

	"github.com/sbinet/go-commander"
	"github.com/sbinet/go-flag"
)

func hwaf_make_cmd_dump_env() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_dump_env,
		UsageLine: "dump-env [options]",
		Short:     "print the environment on STDOUT",
		Long: `
dump-env prints the environment on STDOUT.

ex:
 $ hwaf dump-env
 $ hwaf dump-env -shell=sh
 $ hwaf dump-env -shell=csh
`,
		Flag: *flag.NewFlagSet("hwaf-dump-env", flag.ExitOnError),
		//CustomFlags: true,
	}
	cmd.Flag.Bool("q", false, "only print error and warning messages, all other output will be suppressed")
	cmd.Flag.String("shell", "", "type of shell to print the environment for (default=sh)")
	return cmd
}

func hwaf_run_cmd_dump_env(cmd *commander.Command, args []string) {
	var err error
	n := "hwaf-" + cmd.Name()

	switch len(args) {
	case 0:
		// ok
	default:
		err = fmt.Errorf("%s: does not take any argument\n", n)
		handle_err(err)
	}

	var export_var func(k string) string
	shell := cmd.Flag.Lookup("shell").Value.Get().(string)
	//quiet := cmd.Flag.Lookup("q").Value.Get().(bool)

	if shell == "" {
		shell = "sh"
	}

	switch shell {
	default:
		err = fmt.Errorf("%s: shell of type [%s] is unknown", n, shell)
		handle_err(err)

	case "sh":
		export_var = func(k string) string { return fmt.Sprintf("export %s=", k) }

	case "csh":
		export_var = func(k string) string { return fmt.Sprintf("setenv %s ", k) }
	}

	if export_var == nil {
		err = fmt.Errorf("%s: could find a suitable shell", n)
	}

	bin, err := exec.LookPath(os.Args[0])
	handle_err(err)

	buf := new(bytes.Buffer)
	waf := exec.Command(
		bin, "waf", "dump-env",
	)
	waf.Stdin = os.Stdin
	waf.Stdout = buf
	waf.Stderr = os.Stderr

	err = waf.Run()
	handle_err(err)

	env := make(map[string]string)
	err = json.Unmarshal(buf.Bytes(), &env)
	handle_err(err)

	//fmt.Printf("%v\n", env)
	for k, v := range env {
		if k == "_" || k == "PS1" {
			continue
		}
		fmt.Printf("%s%q\n", export_var(k), v)
	}
	return
}

// EOF
