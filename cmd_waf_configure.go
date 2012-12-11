package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"

	"github.com/sbinet/go-commander"
	"github.com/sbinet/go-flag"
)

func hwaf_make_cmd_waf_configure() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_waf_configure,
		UsageLine: "configure",
		Short:     "configure local project or packages",
		Long: `
configure configures the local project or packages.

ex:
 $ hwaf configure
 $ hwaf configure --prefix=my-install-area
 $ hwaf configure --prefix=my-install-area --with-clhep=/path/to/clhep
`,
		Flag: *flag.NewFlagSet("hwaf-waf-configure", flag.ExitOnError),
	}
	return cmd
}

func hwaf_run_cmd_waf_configure(cmd *commander.Command, args []string) {
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

	subargs := append([]string{"configure"}, args...)
	sub := exec.Command(waf, subargs...)
	sub.Stdout = os.Stdout
	sub.Stderr = os.Stderr
	err = sub.Run()
	handle_err(err)
}

// EOF
