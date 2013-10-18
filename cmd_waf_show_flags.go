package main

import (
	"fmt"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
)

func hwaf_make_cmd_waf_show_flags() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_waf_show_flags,
		UsageLine: "flags [options] [<flag-name> [<flag-name> [...]]]",
		Short:     "show local project's 'flags-name' value",
		Long: `
show flags displays the value of some flags.

ex:
 $ hwaf show flags CXXFLAGS
 ['-O2', '-fPIC', '-pipe', '-ansi', '-Wall', '-W', '-pthread', '-m64', '-Wno-deprecated']

 $ hwaf show flags
`,
		Flag: *flag.NewFlagSet("hwaf-waf-show-flags", flag.ExitOnError),
	}
	return cmd
}

func hwaf_run_cmd_waf_show_flags(cmd *commander.Command, args []string) {
	var err error

	pinfos, err := g_ctx.ProjectInfos()
	handle_err(err)

	switch len(args) {
	case 0:
		args = pinfos.Keys()
	}

	err_stack := []error{}
	for _, k := range args {
		val, err2 := pinfos.Get(k)
		if err2 != nil {
			err_stack = append(err_stack, err2)
			err = err2
			continue
		}

		fmt.Printf("%s=%s\n", k, val)
	}

	if len(err_stack) != 0 {
		for _, err := range err_stack {
			fmt.Printf("**error: %v\n", err)
		}
		handle_err(err)
	}
}

// EOF
