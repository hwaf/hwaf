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
	cmd.Flag.Bool("v", false, "enable verbose output")

	return cmd
}

func hwaf_run_cmd_self_init(cmd *commander.Command, args []string) error {
	var err error
	n := "hwaf-self-" + cmd.Name()

	switch len(args) {
	case 0:
		// ok
	default:
		return fmt.Errorf("%s: does NOT take any argument", n)
	}

	verbose := cmd.Flag.Lookup("v").Value.Get().(bool)

	if verbose {
		fmt.Printf("%s...\n", n)
	}

	hwaf_root := os.Getenv("HWAF_ROOT")
	for _, dir := range []string{g_ctx.Root, hwaf_root} {
		if dir != "" {
			g_ctx.Warnf("you are trying to 'hwaf self init' while running a HWAF_ROOT-based installation\n")
			g_ctx.Warnf("this is like crossing the streams in Ghostbusters (ie: it's bad.)\n")
			g_ctx.Warnf("if you think you know what you are doing, unset HWAF_ROOT and re-run 'hwaf self init'\n")
			return fmt.Errorf("${HWAF_ROOT} was set (%s)", dir)
		}
	}

	// 'hwaf self init' is now dummied out...

	if verbose {
		fmt.Printf("%s... [ok]\n", n)
	}

	return err
}

// EOF
