/*
hwaf manages hep-waf based applications and libraries.

 Subcommands:

 init [directory]

 self-update

 configure

 build/make

 install

 bdist
 bdist-rpm
 bdist-dmg
 bdist-deb

 run

 shell

 setup

 add-pkg <pkg-uri> [<pkg-version>]
 checkout|co == alias(add-pkg)
*/
package main

import (
	"fmt"
	"os"

	"github.com/sbinet/go-commander"
	"github.com/sbinet/go-flag"
)

var g_cmd *commander.Commander

func init() {
	g_cmd = &commander.Commander{
		Name: os.Args[0],
		Commands: []*commander.Command{
			hwaf_make_cmd_init(),
			hwaf_make_cmd_setup(),
			hwaf_make_cmd_checkout(),
			hwaf_make_cmd_version(),

			hwaf_make_cmd_self_init(),
			hwaf_make_cmd_self_update(),

			hwaf_make_cmd_waf(),
			hwaf_make_cmd_waf_configure(),
			hwaf_make_cmd_waf_build(),
			hwaf_make_cmd_waf_install(),
			hwaf_make_cmd_waf_clean(),
			hwaf_make_cmd_waf_distclean(),
			hwaf_make_cmd_waf_shell(),
			hwaf_make_cmd_waf_run(),

			hwaf_make_cmd_waf_show_projects(),
			hwaf_make_cmd_waf_show_pkg_uses(),

			hwaf_make_cmd_pkgmgr_get(),
		},
		Flag: flag.NewFlagSet("hwaf", flag.ExitOnError),
	}
}

func main() {

	if len(os.Args) == 1 && path_exists("wscript") {
		os.Args = append(os.Args, "build", "install")
	}

	// fiddle with environment to allow locate hep-waftools
	hwaf_setup_waf_env()

	err := g_cmd.Flag.Parse(os.Args[1:])
	if err != nil {
		fmt.Printf("**error** %v\n", err)
		os.Exit(1)
	}

	args := g_cmd.Flag.Args()
	err = g_cmd.Run(args)
	if err != nil {
		fmt.Printf("**error** %v\n", err)
		os.Exit(1)
	}

	return
}
