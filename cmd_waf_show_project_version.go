package main

import (
	"fmt"
	"path/filepath"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
	"github.com/hwaf/hwaf/hwaflib"
)

func hwaf_make_cmd_waf_show_project_version() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_waf_show_project_version,
		UsageLine: "project-version",
		Short:     "show local project's version",
		Long: `
show project-version displays the project's version.

ex:
 $ hwaf show project-version
 0.0.1
`,
		Flag: *flag.NewFlagSet("hwaf-waf-show-project-version", flag.ExitOnError),
	}
	return cmd
}

func hwaf_run_cmd_waf_show_project_version(cmd *commander.Command, args []string) {
	var err error
	//n := "hwaf-" + cmd.Name()

	workdir, err := g_ctx.Workarea()
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

	pinfo, err := hwaflib.NewProjectInfo(pinfo_name)
	handle_err(err)
	val, err := pinfo.Get("HWAF_PROJECT_VERSION")
	handle_err(err)

	fmt.Printf("%s\n", val)
}

// EOF
