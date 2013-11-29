package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"time"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
)

func hwaf_make_cmd_waf_bdist_dmg() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_waf_bdist_dmg,
		UsageLine: "bdist-dmg [dmg-name]",
		Short:     "create a DMG from the local project/packages",
		Long: `
bdist-dmg creates a DMG from the local project/packages.

ex:
 $ hwaf bdist-dmg
 $ hwaf bdist-dmg -name=mana
 $ hwaf bdist-dmg -name=mana -version=20130101
`,
		Flag: *flag.NewFlagSet("hwaf-bdist-dmg", flag.ExitOnError),
	}
	cmd.Flag.Bool("v", false, "enable verbose output")
	cmd.Flag.String("name", "", "name of the binary distribution (default: project name)")
	cmd.Flag.String("version", "", "version of the binary distribution (default: project version)")
	cmd.Flag.String("variant", "", "HWAF_VARIANT quadruplet for the binary distribution (default: project variant)")
	return cmd
}

func hwaf_run_cmd_waf_bdist_dmg(cmd *commander.Command, args []string) {
	var err error
	n := "hwaf-" + cmd.Name()

	switch len(args) {
	case 0:
	default:
		err = fmt.Errorf("%s: too many arguments (%s)", n, len(args))
		handle_err(err)
	}

	verbose := cmd.Flag.Lookup("v").Value.Get().(bool)

	bdist_name := cmd.Flag.Lookup("name").Value.Get().(string)
	bdist_vers := cmd.Flag.Lookup("version").Value.Get().(string)
	bdist_variant := cmd.Flag.Lookup("variant").Value.Get().(string)

	workdir, err := g_ctx.Workarea()
	if err != nil {
		// not a git repo... assume we are at the root, then...
		workdir, err = os.Getwd()
	}
	handle_err(err)

	pinfos, err := g_ctx.ProjectInfos()
	handle_err(err)

	if bdist_name == "" {
		bdist_name = workdir
		bdist_name = filepath.Base(bdist_name)
	}
	if bdist_vers == "" {
		bdist_vers = time.Now().Format("20060102")
	}
	if bdist_variant == "" {
		bdist_variant, err = pinfos.Get("HWAF_VARIANT")
		handle_err(err)
	}

	bdist_fname := bdist_name + "-" + bdist_vers + "-" + bdist_variant + ".dmg"

	// first try destdir
	install_area, err := pinfos.Get("DESTDIR")
	if err != nil {
		install_area, err = pinfos.Get("PREFIX")
	}
	handle_err(err)
	if !path_exists(install_area) {
		err = fmt.Errorf(
			"no such directory [%s]. did you run \"hwaf install\" ?",
			install_area,
		)
		handle_err(err)
	}

	if verbose {
		fmt.Printf("%s: building DMG [%s]...[ok]\n", n, bdist_fname)
	}

	hdiutil, err := exec.LookPath("hdiutil")
	handle_err(err)

	dmg := exec.Command(hdiutil,
		"create",
		bdist_fname,
		"-volname", bdist_name+"-"+bdist_vers,
		"-srcfolder", ".",
		"-imagekey", "zlib-level=9",
		"-ov",
	)
	dmg.Dir = install_area

	if verbose {
		dmg.Stdin = os.Stdin
		dmg.Stdout = os.Stdout
		dmg.Stderr = os.Stderr
	}
	err = dmg.Run()
	handle_err(err)

	if verbose {
		fmt.Printf("%s: building DMG [%s]...[ok]\n", n, bdist_fname)
	}
}

// EOF
