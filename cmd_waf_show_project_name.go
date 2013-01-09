package main

import (
	"fmt"
	"path/filepath"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
)

func hwaf_make_cmd_waf_show_project_name() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_waf_show_project_name,
		UsageLine: "project-name",
		Short:     "show local project's name",
		Long: `
show project-name displays the project's name.

ex:
 $ hwaf show project-name
 mana-core
`,
		Flag: *flag.NewFlagSet("hwaf-waf-show-project-name", flag.ExitOnError),
	}
	return cmd
}

func hwaf_run_cmd_waf_show_project_name(cmd *commander.Command, args []string) {
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
	val, err := pinfo.Get("HWAF_PROJECT_NAME")
	handle_err(err)

	fmt.Printf("%s\n", val)
}

// EOF
