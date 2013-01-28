package main

import (
	"fmt"
	"regexp"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
)

func hwaf_make_cmd_pkg_ls() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_pkg_ls,
		UsageLine: "ls [options] [pattern]",
		Short:     "list locally checked out packages",
		Long: `
ls lists the locally checked out packages.

ex:
 $ hwaf pkg ls
 $ hwaf pkg ls ".*?Athena.*?"
`,
		Flag: *flag.NewFlagSet("hwaf-pkg-ls", flag.ExitOnError),
	}
	cmd.Flag.Bool("q", true, "only print error and warning messages, all other output will be suppressed")

	return cmd
}

func hwaf_run_cmd_pkg_ls(cmd *commander.Command, args []string) {
	var err error
	n := "hwaf-pkg-" + cmd.Name()
	pat := ".*?"
	switch len(args) {
	case 0:
		pat = ".*?"
	case 1:
		pat = args[0]
	default:
		err = fmt.Errorf("%s: you need to give a package pattern to list", n)
		handle_err(err)
	}

	quiet := cmd.Flag.Lookup("q").Value.Get().(bool)

	if !quiet {
		fmt.Printf("%s: listing packages [%s]...\n", n, pat)
	}

	re_pkg, err := regexp.Compile(pat)
	handle_err(err)

	pkgs := g_ctx.PkgDb.Pkgs()
	for _, v := range pkgs {
		if re_pkg.MatchString(v) {
			pkg, err := g_ctx.PkgDb.GetPkg(v)
			handle_err(err)
			fmt.Printf("%s (%s)\n", pkg.Path, pkg.Type)
		}
	}

	if !quiet {
		fmt.Printf("%s: listing packages [%s]... [ok]\n", n, pat)
	}
}

// EOF
