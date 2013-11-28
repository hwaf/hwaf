package main

import (
	"fmt"
	"os"
	// "os/exec"
	"path/filepath"
	"time"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
)

func hwaf_make_cmd_waf_bdist() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_waf_bdist,
		UsageLine: "bdist [options]",
		Short:     "create a binary distribution from the project or packages",
		Long: `
bdist creates a binary distribution from the project or packages.

ex:
 $ hwaf bdist
 $ hwaf bdist -name=mana
 $ hwaf bdist -name=mana -version=20121218
 $ hwaf bdist -name=mana -version -variant=x86_64-linux-gcc-opt
`,
		Flag: *flag.NewFlagSet("hwaf-bdist", flag.ExitOnError),
		//CustomFlags: true,
	}
	cmd.Flag.Bool("v", false, "enable verbose output")
	cmd.Flag.String("name", "", "name of the binary distribution (default: project name)")
	cmd.Flag.String("version", "", "version of the binary distribution (default: project version)")
	cmd.Flag.String("variant", "", "HWAF_VARIANT quadruplet for the binary distribution (default: project VARIANT)")
	return cmd
}

func hwaf_run_cmd_waf_bdist(cmd *commander.Command, args []string) {
	var err error
	n := "hwaf-" + cmd.Name()

	switch len(args) {
	case 0:
	default:
		err = fmt.Errorf("%s: too many arguments (%d)", n, len(args))
		handle_err(err)
	}

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
	fname := bdist_name + "-" + bdist_vers + "-" + bdist_variant + ".tar.gz"

	//fmt.Printf(">> fname=[%s]\n", fname)
	fname = filepath.Join(workdir, fname)

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
	// the prefix to prepend inside the tar-ball
	prefix := bdist_name + "-" + bdist_vers //+ "-" + bdist_variant
	// create a temporary install-area with the correct structure:
	//  install-area/<pkgname>-<pkgvers>/...
	bdist_dir := filepath.Join(workdir, ".hwaf-bdist-install-area-"+bdist_variant)
	_ = os.RemoveAll(bdist_dir)
	err = os.MkdirAll(bdist_dir, 0700)
	handle_err(err)

	// move the install-area...
	err = os.Rename(install_area, filepath.Join(bdist_dir, prefix))
	handle_err(err)
	defer func() {
		err = os.Rename(filepath.Join(bdist_dir, prefix), install_area)
		handle_err(err)
		err = os.RemoveAll(bdist_dir)
		handle_err(err)
	}()

	err = _tar_gz(fname, bdist_dir)
	handle_err(err)
}

// EOF
