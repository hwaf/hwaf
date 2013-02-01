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
	"os"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
	"github.com/mana-fwk/hwaf/hwaflib"
)

var g_cmd *commander.Commander
var g_ctx *hwaflib.Context

func init() {
	g_cmd = &commander.Commander{
		Name: os.Args[0],
		Commands: []*commander.Command{
			hwaf_make_cmd_asetup(),
			hwaf_make_cmd_init(),
			hwaf_make_cmd_setup(),
			hwaf_make_cmd_version(),

			hwaf_make_cmd_cmt_cnv(),

			hwaf_make_cmd_waf(),
			hwaf_make_cmd_waf_configure(),
			hwaf_make_cmd_waf_build(),
			hwaf_make_cmd_waf_install(),
			hwaf_make_cmd_waf_clean(),
			hwaf_make_cmd_waf_distclean(),
			hwaf_make_cmd_waf_shell(),
			hwaf_make_cmd_waf_run(),

			hwaf_make_cmd_waf_sdist(),
			hwaf_make_cmd_waf_bdist(),
			hwaf_make_cmd_waf_bdist_deb(),
			hwaf_make_cmd_waf_bdist_rpm(),

			hwaf_make_cmd_dump_env(),
		},
		Flag: flag.NewFlagSet("hwaf", flag.ExitOnError),
		Commanders: []*commander.Commander{
			hwaf_make_cmd_git(),
			hwaf_make_cmd_pkg(),
			hwaf_make_cmd_waf_show(),
			hwaf_make_cmd_pmgr(),
			hwaf_make_cmd_self(),
		},
	}
}

func main() {

	if len(os.Args) == 1 && path_exists("wscript") {
		os.Args = append(os.Args, "waf", "build+install")
	}

	var err error
	g_ctx, err = hwaflib.NewContext()
	handle_err(err)

	err = g_cmd.Flag.Parse(os.Args[1:])
	handle_err(err)

	args := g_cmd.Flag.Args()
	err = g_cmd.Run(args)
	handle_err(err)

	return
}
