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
	cmd.Flag.Bool("v", false, "enable verbose output")

	return cmd
}

func hwaf_run_cmd_pkg_ls(cmd *commander.Command, args []string) error {
	var err error
	n := "hwaf-pkg-" + cmd.Name()
	pat := ".*?"
	switch len(args) {
	case 0:
		pat = ".*?"
	case 1:
		pat = args[0]
	default:
		return fmt.Errorf("%s: you need to give a package pattern to list", n)
	}

	verbose := cmd.Flag.Lookup("v").Value.Get().(bool)

	if verbose {
		fmt.Printf("%s: listing packages [%s]...\n", n, pat)
	}

	re_pkg, err := regexp.Compile(pat)
	if err != nil {
		return err
	}

	pkgs := g_ctx.PkgDb.Pkgs()
	for _, v := range pkgs {
		if re_pkg.MatchString(v) {
			pkg, err := g_ctx.PkgDb.GetPkg(v)
			if err != nil {
				return err
			}
			fmt.Printf("%s (%s)\n", pkg.Path, pkg.Type)
		}
	}

	if verbose {
		fmt.Printf("%s: listing packages [%s]... [ok]\n", n, pat)
	}

	return err
}

// EOF
