package main_test

import (
	"io/ioutil"
	"os"
	"testing"
)

func TestWorchVcs(t *testing.T) {

	workdir, err := ioutil.TempDir("", "hwaf-test-")
	if err != nil {
		t.Fatalf(err.Error())
	}
	defer os.RemoveAll(workdir)
	//fmt.Printf(">>> test: %s\n", workdir)

	err = os.Chdir(workdir)
	if err != nil {
		t.Fatalf(err.Error())
	}

	hwaf, err := newlogger("hwaf.log")
	if err != nil {
		t.Fatalf(err.Error())
	}
	defer hwaf.Close()

	const worch_cfg_tmpl = `
# test the vcs feature
[start]
groups = vcs
group = vcs
features = vcs autoconf makemake

# Tags
tags = debug

# not actually used for vcs...
download_dir = downloads

source_dir = sources
build_dir = builds/{package}-{version}-{tagsdashed}
install_dir = {PREFIX}/{package}/{version}/{tagsdashed}
source_unpacked = {package}-{version}.{vcs_flavor}
unpacked_target = autogen.sh
vcs_flavor = git

[group vcs]
packages = cjson

[package cjson]
version = master
source_url = git://github.com/chefpeyo/cJSON.git
vcs_tag = {version}
prepare_cmd = cp -r ../../{source_dir}/{source_unpacked}/* . && ./autogen.sh
prepare_target = config.status
build_target = src/lib/libcjson.la
install_target = lib/libcjson.so


[keytype]
groups = group
packages = package
`
	f, err := os.Create("worch.cfg")
	if err != nil {
		t.Fatalf("error creating worch.cfg: %v\n", err)
	}
	defer f.Close()

	_, err = f.WriteString(worch_cfg_tmpl)
	if err != nil {
		t.Fatalf("error generating worch.cfg: %v\n", err)
	}

	// build
	for _, cmd := range [][]string{
		{"hwaf", "init", "-v=1", "."},
		{"hwaf", "setup", "-v=1", "."},
		{"hwaf", "configure", "--prefix=" + workdir + "/install"},
		{"hwaf"},
	} {
		err := hwaf.Run(cmd[0], cmd[1:]...)
		if err != nil {
			hwaf.Display()
			t.Fatalf("cmd %v failed: %v", cmd, err)
		}
	}
}

func TestWorchAutoconf(t *testing.T) {
	workdir, err := ioutil.TempDir("", "hwaf-test-")
	if err != nil {
		t.Fatalf(err.Error())
	}
	//defer os.RemoveAll(workdir)
	//fmt.Printf(">>> test: %s\n", workdir)

	err = os.Chdir(workdir)
	if err != nil {
		t.Fatalf(err.Error())
	}

	hwaf, err := newlogger("hwaf.log")
	if err != nil {
		t.Fatalf(err.Error())
	}
	defer hwaf.Close()

	const worch_cfg_tmpl = `
# Simple example orch.cfg file for installing a suite of software
# packages.  An artificial dependency is setup so that hello "depends"
# on "bc".

# Note: additional interpolation is done by the waf scripts so some
# variable may appear to be undefined but will be satisfied later.

# The default starting section
[start]
# A comma-separated list of groups of packages.
groups = gnuprograms

# Default group
group = gnuprograms

# Tags
tags = debug

# The (default) features of a package build. Should be
# space-separated.  Depending on what feature is active for a package
# different variables are required to exist.  
#features = dumpenv tarball autoconf
features = tarball autoconf makemake

# where tarballs or other source packages get downloaded
download_dir = downloads

# top directory holding unpacked source directories
source_dir = sources

# top directory where a build occurs.  {tagsdashed} is provided by the
# application.
build_dir = builds/{package}-{version}-{tagsdashed}

# Installation area for the package 
install_dir = {PREFIX}/{package}/{version}/{tagsdashed}

# Depending on the feature, certain variables must be provided
srcpkg_ext = tar.gz
source_unpacked = {package}-{version}
source_package = {source_unpacked}.{srcpkg_ext}


# This section defines the schema of the configuration itself.  It is
# required to be found in the configuration and should only be
# modified by experts.  Worch requires "groups" and "packages".
[keytype]
groups = group
packages = package

[group gnuprograms]
# Comma separated list of tags which should be honored when building
# the package.  They may be used to dermine output locations where the
# derived "tagsdashed" variable may be useful

# A list of packages to build.  Note: "packages" is a keytype
packages = hello, bc

# set a common URL pattern for all gnu programs
source_url = http://ftp.gnu.org/gnu/{package}/{source_package}

# artificially require any environment variables defined by package or
# groups of packages.  This example redundantly required cmake twice
# since it's part of the buildtools group
unpacked_target = configure
prepare_target = config.status

[package hello]
version = 2.8

# dependencies can be expressed as a comma-separated list.  Each
# element is a package name or a <step>:<package>_<step> pair.  The
# former will require the dependency to be fully installed before the
# current package is started.  The latter sets up a fine-grained
# dependecy requiring <package>_<step> to complete before this
# package's <step> is started.
depends = prepare:bc_install
build_target = src/hello
install_target = bin/hello

[package bc]
version = 1.06 
build_target = bc/bc
install_target = bin/bc
`
	f, err := os.Create("worch.cfg")
	if err != nil {
		t.Fatalf("error creating worch.cfg: %v\n", err)
	}
	defer f.Close()

	_, err = f.WriteString(worch_cfg_tmpl)
	if err != nil {
		t.Fatalf("error generating worch.cfg: %v\n", err)
	}

	// build
	for _, cmd := range [][]string{
		{"hwaf", "init", "-v=1", "."},
		{"hwaf", "setup", "-v=1", "."},
		{"hwaf", "configure", "--prefix=" + workdir + "/install"},
		{"hwaf", "build", "install", "--zones=orch"},
	} {
		err := hwaf.Run(cmd[0], cmd[1:]...)
		if err != nil {
			hwaf.Display()
			t.Fatalf("cmd %v failed: %v", cmd, err)
		}
	}
}

// EOF
