package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
)

func hwaf_make_cmd_waf_clean() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_waf_clean,
		UsageLine: "clean",
		Short:     "clean local project or packages",
		Long: `
clean cleans the local project or packages.

ex:
 $ hwaf clean
`,
		Flag:        *flag.NewFlagSet("hwaf-waf-clean", flag.ExitOnError),
		CustomFlags: true,
	}
	return cmd
}

func hwaf_run_cmd_waf_clean(cmd *commander.Command, args []string) {
	var err error
	//n := "hwaf-" + cmd.Name()

	top := hwaf_root()
	waf := filepath.Join(top, "bin", "waf")
	if !path_exists(waf) {
		err = fmt.Errorf(
			"no such file [%s]\nplease re-run 'hwaf self-init'\n",
			waf,
		)
		handle_err(err)
	}

	subargs := append([]string{"clean"}, args...)
	sub := exec.Command(waf, subargs...)
	sub.Stdout = os.Stdout
	sub.Stderr = os.Stderr
	err = sub.Run()
	handle_err(err)
}

// EOF
