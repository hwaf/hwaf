package main

import (
	"os"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
)

func hwaf_make_cmd_waf_show_pkg_tree() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_waf_show_pkg_tree,
		UsageLine: "pkg-tree",
		Short:     "show local project's packages dependency tree",
		Long: `
show pkg-tree displays the dependency tree of a given project.

ex:
 $ hwaf show pkg-tree
 $ hwaf show pkg-tree AtlasOffline
`,
		Flag:        *flag.NewFlagSet("hwaf-waf-show-pkg-tree", flag.ExitOnError),
		CustomFlags: true,
	}
	return cmd
}

func hwaf_run_cmd_waf_show_pkg_tree(cmd *commander.Command, args []string) {
	var err error
	//n := "hwaf-" + cmd.Name()

	waf, err := g_ctx.WafBin()
	handle_err(err)

	subargs := append([]string{"show-pkg-tree"}, args...)
	sub := g_ctx.Command(waf, subargs...)
	sub.Stdout = os.Stdout
	sub.Stderr = os.Stderr
	err = sub.Run()
	handle_err(err)
}

// EOF
