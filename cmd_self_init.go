package main

import (
	"fmt"
	"os"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
)

func hwaf_make_cmd_self_init() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_self_init,
		UsageLine: "init [options] <workarea>",
		Short:     "initialize hwaf itself",
		Long: `
init initializes hwaf internal files.

ex:
 $ hwaf self init
`,
		Flag: *flag.NewFlagSet("hwaf-self-init", flag.ExitOnError),
	}
	cmd.Flag.Bool("q", true, "only print error and warning messages, all other output will be suppressed")

	return cmd
}

func hwaf_run_cmd_self_init(cmd *commander.Command, args []string) {
	var err error
	n := "hwaf-self-" + cmd.Name()

	switch len(args) {
	case 0:
		// ok
	default:
		err = fmt.Errorf("%s: does NOT take any argument", n)
		handle_err(err)
	}

	quiet := cmd.Flag.Lookup("q").Value.Get().(bool)

	if !quiet {
		fmt.Printf("%s...\n", n)
	}

	hwaf_root := os.Getenv("HWAF_ROOT")
	for _, dir := range []string{g_ctx.Root, hwaf_root} {
		if dir != "" {
			g_ctx.Warn("you are trying to 'hwaf self init' while running a HWAF_ROOT-based installation\n")
			g_ctx.Warn("this is like crossing the streams in Ghostbusters (ie: it's bad.)\n")
			g_ctx.Warn("if you think you know what you are doing, unset HWAF_ROOT and re-run 'hwaf self init'\n")
			err = fmt.Errorf("${HWAF_ROOT} was set (%s)", dir)
			handle_err(err)
		}
	}

	// 'hwaf self init' is now dummied out...

	if !quiet {
		fmt.Printf("%s... [ok]\n", n)
	}
}

// EOF
