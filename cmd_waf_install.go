package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"

	"github.com/sbinet/go-commander"
	"github.com/sbinet/go-flag"
)

func hwaf_make_cmd_waf_install() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_waf_install,
		UsageLine: "install",
		Short:     "install local project or packages",
		Long: `
install installs the local project or packages.

ex:
 $ hwaf install
 $ hwaf install --prefix=my-install-area
 $ hwaf install --prefix=my-install-area --destdir=/tmp/dest
`,
		Flag: *flag.NewFlagSet("hwaf-waf-install", flag.ExitOnError),
	}
	return cmd
}

func hwaf_run_cmd_waf_install(cmd *commander.Command, args []string) {
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

	subargs := append([]string{"install"}, args...)
	sub := exec.Command(waf, subargs...)
	sub.Stdout = os.Stdout
	sub.Stderr = os.Stderr
	err = sub.Run()
	handle_err(err)
}

// EOF
