package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"

	"github.com/sbinet/go-commander"
	"github.com/sbinet/go-flag"
)

func hwaf_make_cmd_waf_distclean() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_waf_distclean,
		UsageLine: "distclean",
		Short:     "distclean local project or packages",
		Long: `
distclean removes the build directory of the local project or packages.

ex:
 $ hwaf distclean
`,
		Flag: *flag.NewFlagSet("hwaf-waf-distclean", flag.ExitOnError),
	}
	return cmd
}

func hwaf_run_cmd_waf_distclean(cmd *commander.Command, args []string) {
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

	subargs := append([]string{"distclean"}, args...)
	sub := exec.Command(waf, subargs...)
	sub.Stdout = os.Stdout
	sub.Stderr = os.Stderr
	err = sub.Run()
	handle_err(err)
}

// EOF