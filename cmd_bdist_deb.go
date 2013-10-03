package main

import (
	"fmt"
	"io"
	"io/ioutil"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"text/template"
	"time"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
	"github.com/hwaf/hwaf/hwaflib"
)

func hwaf_make_cmd_waf_bdist_deb() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_waf_bdist_deb,
		UsageLine: "bdist-deb [deb-name]",
		Short:     "create a DEB from the local project/packages",
		Long: `
bdist-deb creates a DEB from the local project/packages.

ex:
 $ hwaf bdist-deb
 $ hwaf bdist-deb -name=mana
 $ hwaf bdist-deb -name=mana -version=20130101
`,
		Flag: *flag.NewFlagSet("hwaf-bdist-deb", flag.ExitOnError),
	}
	cmd.Flag.Bool("v", false, "enable verbose output")
	cmd.Flag.String("name", "", "name of the binary distribution (default: project name)")
	cmd.Flag.String("version", "", "version of the binary distribution (default: project version)")
	cmd.Flag.String("release", "1", "release version of the binary distribution (default: 1)")
	cmd.Flag.String("variant", "", "HWAF_VARIANT quadruplet for the binary distribution (default: project variant)")
	cmd.Flag.String("spec", "", "DEB control file for the binary distribution")
	cmd.Flag.String("url", "", "URL for the DEB binary distribution")
	return cmd
}

func hwaf_run_cmd_waf_bdist_deb(cmd *commander.Command, args []string) {
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
	bdist_release := cmd.Flag.Lookup("release").Value.Get().(string)
	bdist_variant := cmd.Flag.Lookup("variant").Value.Get().(string)
	bdist_spec := cmd.Flag.Lookup("spec").Value.Get().(string)

	bdist_url := cmd.Flag.Lookup("url").Value.Get().(string)
	if bdist_url == "" {
		bdist_url = "http://cern.ch/mana-fwk"
	}

	type DebInfo struct {
		Name      string // DEB package name
		Vers      string // DEB package version
		Release   string // DEB package release
		Variant   string // DEB VARIANT quadruplet
		BuildRoot string // DEB build directory
		Url       string // URL home page
		Arch      string // DEB architecture (32b/64b)
	}

	workdir, err := g_ctx.Workarea()
	if err != nil {
		// not a git repo... assume we are at the root, then...
		workdir, err = os.Getwd()
	}
	handle_err(err)

	if bdist_name == "" {
		bdist_name = workdir
		bdist_name = filepath.Base(bdist_name)
	}
	if bdist_vers == "" {
		bdist_vers = time.Now().Format("20060102")
	}
	if bdist_variant == "" {
		// FIXME: get actual value from waf, somehow
		pinfo_name := filepath.Join(workdir, "__build__", "c4che", "_cache.py")
		if !path_exists(pinfo_name) {
			err = fmt.Errorf(
				"no such file [%s]. did you run \"hwaf configure\" ?",
				pinfo_name,
			)
			handle_err(err)
		}
		pinfo, err := hwaflib.NewProjectInfo(pinfo_name)
		handle_err(err)
		bdist_variant, err = pinfo.Get("HWAF_VARIANT")
		handle_err(err)
	}
	fname := bdist_name + "-" + bdist_vers + "-" + bdist_variant
	debtopdir, err := ioutil.TempDir("", "hwaf-deb-buildroot-")
	handle_err(err)
	defer os.RemoveAll(debtopdir)

	debbldroot := filepath.Join(debtopdir, "debian")
	err = os.MkdirAll(debbldroot, 0755)
	handle_err(err)

	for _, dir := range []string{
		"DEBIAN",
	} {
		err = os.MkdirAll(filepath.Join(debbldroot, dir), 0755)
		handle_err(err)
	}

	specfile, err := os.Create(filepath.Join(debbldroot, "DEBIAN", "control"))
	handle_err(err)

	debarch := ""
	switch runtime.GOARCH {
	case "amd64":
		debarch = "amd64"
	case "386":
		debarch = "i386"
	default:
		err = fmt.Errorf("unhandled GOARCH [%s]", runtime.GOARCH)
		handle_err(err)
	}

	debinfos := DebInfo{
		Name:      bdist_name,
		Vers:      bdist_vers,
		Release:   bdist_release,
		Variant:   bdist_variant,
		BuildRoot: debbldroot,
		Url:       bdist_url,
		Arch:      debarch,
	}

	// get tarball from 'hwaf bdist'...
	bdist_fname := strings.Replace(fname, ".deb", "", 1) + ".tar.gz"
	if !path_exists(bdist_fname) {
		err = fmt.Errorf("no such file [%s]. did you run \"hwaf bdist\" ?", bdist_fname)
		handle_err(err)
	}
	bdist_fname, err = filepath.Abs(bdist_fname)
	handle_err(err)
	{
		untar := exec.Command("tar", "-zxf", bdist_fname, "--strip", "1")
		untar.Dir = debbldroot
		untar.Stdin = os.Stdin
		untar.Stdout = os.Stdout
		untar.Stderr = os.Stderr
		err = untar.Run()
		handle_err(err)
	}

	if bdist_spec != "" {
		bdist_spec = os.ExpandEnv(bdist_spec)
		bdist_spec, err = filepath.Abs(bdist_spec)
		handle_err(err)

		if !path_exists(bdist_spec) {
			err = fmt.Errorf("no such file [%s]", bdist_spec)
			handle_err(err)
		}
		user_spec, err := os.Open(bdist_spec)
		handle_err(err)
		defer user_spec.Close()

		_, err = io.Copy(specfile, user_spec)
		handle_err(err)
	} else {
		bdist_spec = specfile.Name()

		var spec_tmpl *template.Template
		spec_tmpl, err = template.New("SPEC").Parse(`
Package: {{.Name}}
Version: {{.Vers}}-{{.Release}}
Section: devel
Priority: optional
Architecture: {{.Arch}}
Depends: coreutils
Maintainer: hwaf
Description: hwaf generated DEB for {{.Name}}
`) // */ for emacs...
		handle_err(err)

		err = spec_tmpl.Execute(specfile, debinfos)
		handle_err(err)
	}

	err = specfile.Sync()
	handle_err(err)
	err = specfile.Close()
	handle_err(err)

	if !strings.HasSuffix(fname, ".deb") {
		fname = fname + ".deb"
	}

	if verbose {
		fmt.Printf("%s: building DEB [%s]...\n", n, fname)
	}

	debbld, err := exec.LookPath("dpkg-deb")
	handle_err(err)
	//dpkg-deb --build debian
	deb := exec.Command(debbld,
		"--build",
		"debian",
	)
	deb.Dir = debtopdir
	if verbose {
		deb.Stdin = os.Stdin
		deb.Stdout = os.Stdout
		deb.Stderr = os.Stderr
	}
	err = deb.Run()
	handle_err(err)

	dst, err := os.Create(fname)
	handle_err(err)
	defer dst.Close()

	src, err := os.Open(filepath.Join(debtopdir, "debian.deb"))
	handle_err(err)
	defer src.Close()

	_, err = io.Copy(dst, src)
	handle_err(err)
	err = dst.Sync()
	handle_err(err)

	if verbose {
		fmt.Printf("%s: building DEB [%s]...[ok]\n", n, fname)
	}
}

// EOF
