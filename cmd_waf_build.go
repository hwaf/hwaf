package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"

	"github.com/sbinet/go-commander"
	"github.com/sbinet/go-flag"
)

func hwaf_make_cmd_waf_build() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_waf_build,
		UsageLine: "build",
		Short:     "build local project or packages",
		Long: `
build builds the local project or packages.

ex:
 $ hwaf build
 $ hwaf build --prefix=my-install-area
 $ hwaf build --prefix=my-install-area --destdir=/tmp/dest
`,
		Flag: *flag.NewFlagSet("hwaf-waf-build", flag.ExitOnError),
		CustomFlags: true,
	}
	return cmd
}

func hwaf_run_cmd_waf_build(cmd *commander.Command, args []string) {
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

	subargs := append([]string{"build"}, args...)
	sub := exec.Command(waf, subargs...)
	sub.Stdout = os.Stdout
	sub.Stderr = os.Stderr
	err = sub.Run()
	handle_err(err)
}

// EOF
