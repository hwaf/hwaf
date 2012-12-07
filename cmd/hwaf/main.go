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
		},
		Flag: flag.NewFlagSet("hwaf", flag.ExitOnError),
	}
}

func main() {

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
