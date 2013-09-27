package main

import (
	"fmt"
	"path/filepath"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
	"github.com/hwaf/hwaf/hwaflib"
)

func hwaf_make_cmd_waf_show_active_tags() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_waf_show_active_tags,
		UsageLine: "active-tags [options]",
		Short:     "show list of active tags for the local project",
		Long: `
show list of active tags for the local project.

ex:
 $ hwaf show active-tags
 ['target-slc6', 'opt']

`,
		Flag: *flag.NewFlagSet("hwaf-waf-show-active-tags", flag.ExitOnError),
	}
	return cmd
}

func hwaf_run_cmd_waf_show_active_tags(cmd *commander.Command, args []string) {
	var err error

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

	val, err := pinfo.Get("HWAF_ACTIVE_TAGS")
	handle_err(err)
	fmt.Printf("%s\n", val)
}

// EOF
