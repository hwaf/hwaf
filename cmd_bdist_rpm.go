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
)

func hwaf_make_cmd_waf_bdist_rpm() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_waf_bdist_rpm,
		UsageLine: "bdist-rpm [rpm-name]",
		Short:     "create a RPM from the local project/packages",
		Long: `
bdist-rpm creates a RPM from the local project/packages.

ex:
 $ hwaf bdist-rpm
 $ hwaf bdist-rpm -name=mana
 $ hwaf bdist-rpm -name=mana -version=20130101
`,
		Flag: *flag.NewFlagSet("hwaf-bdist-rpm", flag.ExitOnError),
	}
	cmd.Flag.Bool("v", false, "enable verbose output")
	cmd.Flag.String("name", "", "name of the binary distribution (default: project name)")
	cmd.Flag.String("version", "", "version of the binary distribution (default: project version)")
	cmd.Flag.String("release", "1", "release version of the binary distribution (default: 1)")
	cmd.Flag.String("variant", "", "HWAF_VARIANT quadruplet for the binary distribution (default: project variant)")
	cmd.Flag.String("spec", "", "RPM SPEC file for the binary distribution")
	cmd.Flag.String("url", "", "URL for the RPM binary distribution")
	return cmd
}

func hwaf_run_cmd_waf_bdist_rpm(cmd *commander.Command, args []string) error {
	var err error
	n := "hwaf-" + cmd.Name()

	switch len(args) {
	case 0:
	default:
		return fmt.Errorf("%s: too many arguments (%s)", n, len(args))
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

	type RpmInfo struct {
		Name      string // RPM package name
		Vers      string // RPM package version
		Release   string // RPM package release
		Variant   string // RPM VARIANT quadruplet
		BuildRoot string // RPM build directory
		Url       string // URL home page
	}

	workdir, err := g_ctx.Workarea()
	if err != nil {
		// not a git repo... assume we are at the root, then...
		workdir, err = os.Getwd()
	}
	if err != nil {
		return err
	}

	if bdist_name == "" {
		bdist_name = workdir
		bdist_name = filepath.Base(bdist_name)
	}
	if bdist_vers == "" {
		bdist_vers = time.Now().Format("20060102")
	}
	if bdist_variant == "" {
		pinfo, err := g_ctx.ProjectInfos()
		if err != nil {
			return err
		}
		bdist_variant, err = pinfo.Get("HWAF_VARIANT")
		if err != nil {
			return err
		}
	}
	fname := bdist_name + "-" + bdist_vers + "-" + bdist_variant
	rpmbldroot, err := ioutil.TempDir("", "hwaf-rpm-buildroot-")
	if err != nil {
		return err
	}
	defer os.RemoveAll(rpmbldroot)
	for _, dir := range []string{
		"RPMS", "SRPMS", "BUILD", "SOURCES", "SPECS", "tmp",
	} {
		err = os.MkdirAll(filepath.Join(rpmbldroot, dir), 0700)
		if err != nil {
			return err
		}
	}

	specfile, err := os.Create(filepath.Join(rpmbldroot, "SPECS", bdist_name+".spec"))
	if err != nil {
		return err
	}

	rpminfos := RpmInfo{
		Name:      bdist_name,
		Vers:      bdist_vers,
		Release:   bdist_release,
		Variant:   bdist_variant,
		BuildRoot: rpmbldroot,
		Url:       bdist_url,
	}

	// get tarball from 'hwaf bdist'...
	bdist_fname := strings.Replace(fname, ".rpm", "", 1) + ".tar.gz"
	if !path_exists(bdist_fname) {
		return fmt.Errorf("no such file [%s]. did you run \"hwaf bdist\" ?", bdist_fname)
	}
	bdist_fname, err = filepath.Abs(bdist_fname)
	if err != nil {
		return err
	}
	{
		// first, massage the tar ball to something rpmbuild expects...

		// ok, now we're done.
		dst, err := os.Create(filepath.Join(rpmbldroot, "SOURCES", filepath.Base(bdist_fname)))
		if err != nil {
			return err
		}
		src, err := os.Open(bdist_fname)
		if err != nil {
			return err
		}
		_, err = io.Copy(dst, src)
		if err != nil {
			return err
		}
	}

	if bdist_spec != "" {
		bdist_spec = os.ExpandEnv(bdist_spec)
		bdist_spec, err = filepath.Abs(bdist_spec)
		if err != nil {
			return err
		}

		if !path_exists(bdist_spec) {
			return fmt.Errorf("no such file [%s]", bdist_spec)
		}
		user_spec, err := os.Open(bdist_spec)
		if err != nil {
			return err
		}
		defer user_spec.Close()

		_, err = io.Copy(specfile, user_spec)
		if err != nil {
			return err
		}
	} else {
		bdist_spec = specfile.Name()

		var spec_tmpl *template.Template
		spec_tmpl, err = template.New("SPEC").Parse(`
%define __spec_install_post %{nil}
%define   debug_package %{nil}
%define __os_install_post %{_dbpath}/brp-compress
%define   variant {{.Variant}}
%define _topdir {{.BuildRoot}}
%define _tmppath  %{_topdir}/tmp

Summary: hwaf generated RPM for {{.Name}}
Name: {{.Name}}
Version: {{.Vers}}
Release: {{.Release}}
License: Unknown
Group: Development/Tools
SOURCE0 : %{name}-%{version}-%{variant}.tar.gz
URL: {{.Url}}

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root

%description
%{summary}

%prep
%setup -q

%build
# Empty section.

%install
rm -rf %{buildroot}
mkdir -p  %{buildroot}

# in builddir
cp -a * %{buildroot}


%clean
rm -rf %{buildroot}


%files
%defattr(-,root,root,-)
/*
`) // */ for emacs...
		if err != nil {
			return err
		}

		err = spec_tmpl.Execute(specfile, rpminfos)
		if err != nil {
			return err
		}
	}

	err = specfile.Sync()
	if err != nil {
		return err
	}
	err = specfile.Close()
	if err != nil {
		return err
	}

	if !strings.HasSuffix(fname, ".rpm") {
		fname = fname + ".rpm"
	}

	if verbose {
		fmt.Printf("%s: building RPM [%s]...\n", n, fname)
	}

	rpmbld, err := exec.LookPath("rpmbuild")
	if err != nil {
		return err
	}

	rpm := exec.Command(rpmbld,
		"-bb",
		filepath.Join("SPECS", rpminfos.Name+".spec"),
	)
	rpm.Dir = rpmbldroot
	if verbose {
		rpm.Stdin = os.Stdin
		rpm.Stdout = os.Stdout
		rpm.Stderr = os.Stderr
	}
	err = rpm.Run()
	if err != nil {
		return err
	}

	dst, err := os.Create(fname)
	if err != nil {
		return err
	}
	defer dst.Close()

	rpmarch := ""
	switch runtime.GOARCH {
	case "amd64":
		rpmarch = "x86_64"
	case "386":
		rpmarch = "i386"
	default:
		return fmt.Errorf("unhandled GOARCH [%s]", runtime.GOARCH)
	}
	srcname := fmt.Sprintf(
		"%s-%s-%s.%s.rpm",
		rpminfos.Name,
		rpminfos.Vers,
		rpminfos.Release,
		rpmarch)

	src, err := os.Open(filepath.Join(rpmbldroot, "RPMS", rpmarch, srcname))
	if err != nil {
		return err
	}
	defer src.Close()

	_, err = io.Copy(dst, src)
	if err != nil {
		return err
	}
	err = dst.Sync()
	if err != nil {
		return err
	}

	if verbose {
		fmt.Printf("%s: building RPM [%s]...[ok]\n", n, fname)
	}

	return nil
}

// EOF
