package main

import (
	"fmt"
	"path/filepath"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
)

func hwaf_make_cmd_waf_show_cmtcfg() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_waf_show_cmtcfg,
		UsageLine: "cmtcfg",
		Short:     "show local project's CMTCFG value",
		Long: `
show cmtcfg displays the project's CMTCFG value.

ex:
 $ hwaf show cmtcfg
 x86_64-linux-gcc-opt
`,
		Flag: *flag.NewFlagSet("hwaf-waf-show-cmtcfg", flag.ExitOnError),
	}
	return cmd
}

func hwaf_run_cmd_waf_show_cmtcfg(cmd *commander.Command, args []string) {
	var err error
	//n := "hwaf-" + cmd.Name()

	workdir, err := get_workarea_root()
	handle_err(err)

	// FIXME: get actual value from waf, somehow
	pinfo_name := filepath.Join(workdir, "__build__", "c4che", "_cache.py")
	if !path_exists(pinfo_name) {
		err = fmt.Errorf(
			"no such file [%s]. did you run \"hwaf configure\" ?",
			pinfo_name,
		)
		handle_err(err)
	}

	pinfo, err := NewProjectInfo(pinfo_name)
	handle_err(err)
	cmtcfg, err := pinfo.Get("CMTCFG")
	handle_err(err)

	fmt.Printf("%s\n", cmtcfg)
}

// EOF
