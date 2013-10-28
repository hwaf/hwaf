package main_test

import (
	"io"
	"io/ioutil"
	"os"
	"path/filepath"
	"testing"
)

func TestHwafBoost(t *testing.T) {
	workdir, err := ioutil.TempDir("", "hwaf-test-")
	if err != nil {
		t.Fatalf(err.Error())
	}
	defer os.RemoveAll(workdir)

	err = os.Chdir(workdir)
	if err != nil {
		t.Fatalf(err.Error())
	}

	hwaf, err := newlogger("hwaf.log")
	if err != nil {
		t.Fatalf(err.Error())
	}
	defer hwaf.Close()

	for _, cmd := range [][]string{
		{"hwaf", "init", "-v=1", "."},
		{"hwaf", "setup", "-v=1"},
		{"hwaf", "pkg", "create", "-script=py", "-v=1", "mypkg"},
		{"hwaf", "pkg", "ls"},
	} {
		err := hwaf.Run(cmd[0], cmd[1:]...)
		if err != nil {
			hwaf.Display()
			t.Fatalf("cmd %v failed: %v", cmd, err)
		}
	}

	mypkgdir := filepath.Join("src", "mypkg")

	// create src/mytools/mypkg/hscript.py file
	ff, err := os.Create(filepath.Join(mypkgdir, "hscript.py"))
	if err != nil {
		t.Fatalf(err.Error())
	}
	_, err = ff.WriteString(
		`
# -*- python -*-
# automatically generated hscript

import waflib.Logs as msg

PACKAGE = {
    'name': 'mypkg',
    'author': ["Sebastien Binet"], 
}

def pkg_deps(ctx):
    # put your package dependencies here.
    # e.g.:
    # ctx.use_pkg('AtlasPolicy')
    return

def options(ctx):
    ctx.load('find_boost')

def configure(ctx):
    ctx.load('find_python')
    ctx.load('find_boost')
    ctx.find_boost(lib='filesystem system', libs="/foo/not/there")
    ctx.start_msg("was Boost found ?")
    ctx.end_msg(ctx.env.HWAF_FOUND_BOOST)
    if ctx.env.HWAF_FOUND_BOOST:
        ctx.start_msg("boost version")
        ctx.end_msg(ctx.env.BOOST_VERSION)
    else:
        msg.fatal("Boost could not be found")

def build(ctx):
    return

`)
	if err != nil {
		t.Fatalf(err.Error())
	}

	ff.Sync()
	ff.Close()

	for _, cmd := range [][]string{
		{"hwaf", "configure"},
		{"hwaf"},
	} {
		err := hwaf.Run(cmd[0], cmd[1:]...)
		if err != nil {
			hwaf.Display()
			cfglog := filepath.Join(workdir, "__build__", "config.log")
			cfg, err2 := os.Open(cfglog)
			if err2 == nil {
				defer cfg.Close()
				io.Copy(os.Stderr, cfg)
			}
			t.Fatalf("cmd %v failed: %v", cmd, err)
		}
	}
}

func TestHwafBoostBogusConfigureCmd(t *testing.T) {
	workdir, err := ioutil.TempDir("", "hwaf-test-")
	if err != nil {
		t.Fatalf(err.Error())
	}
	defer os.RemoveAll(workdir)

	err = os.Chdir(workdir)
	if err != nil {
		t.Fatalf(err.Error())
	}

	hwaf, err := newlogger("hwaf.log")
	if err != nil {
		t.Fatalf(err.Error())
	}
	defer hwaf.Close()

	for _, cmd := range [][]string{
		{"hwaf", "init", "-v=1", "."},
		{"hwaf", "setup", "-v=1"},
		{"hwaf", "pkg", "create", "-script=py", "-v=1", "mypkg"},
		{"hwaf", "pkg", "ls"},
	} {
		err := hwaf.Run(cmd[0], cmd[1:]...)
		if err != nil {
			hwaf.Display()
			t.Fatalf("cmd %v failed: %v", cmd, err)
		}
	}

	mypkgdir := filepath.Join("src", "mypkg")

	// create src/mytools/mypkg/hscript.py file
	ff, err := os.Create(filepath.Join(mypkgdir, "hscript.py"))
	if err != nil {
		t.Fatalf(err.Error())
	}
	_, err = ff.WriteString(
		`
# -*- python -*-
# automatically generated hscript

import waflib.Logs as msg

PACKAGE = {
    'name': 'mypkg',
    'author': ["Sebastien Binet"], 
}

def pkg_deps(ctx):
    # put your package dependencies here.
    # e.g.:
    # ctx.use_pkg('AtlasPolicy')
    return

def options(ctx):
    ctx.load('find_boost')

def configure(ctx):
    ctx.load('find_python')
    ctx.load('find_boost')
    ctx.find_boost(lib='filesystem system')
    ctx.start_msg("was Boost found ?")
    ctx.end_msg(ctx.env.HWAF_FOUND_BOOST)
    if ctx.env.HWAF_FOUND_BOOST:
        ctx.start_msg("boost version")
        ctx.end_msg(ctx.env.BOOST_VERSION)
    else:
        msg.fatal("Boost could not be found")

def build(ctx):
    return

`)
	if err != nil {
		t.Fatalf(err.Error())
	}

	ff.Sync()
	ff.Close()

	for _, cmd := range [][]string{
		{"hwaf", "configure", "--boost-libs=/bar"},
		{"hwaf"},
	} {
		err := hwaf.Run(cmd[0], cmd[1:]...)
		if err != nil {
			hwaf.Display()
			cfglog := filepath.Join(workdir, "__build__", "config.log")
			cfg, err2 := os.Open(cfglog)
			if err2 == nil {
				defer cfg.Close()
				io.Copy(os.Stderr, cfg)
			}
			t.Fatalf("cmd %v failed: %v", cmd, err)
		}
	}
}

func TestHwafBoostEmptyLib(t *testing.T) {
	workdir, err := ioutil.TempDir("", "hwaf-test-")
	if err != nil {
		t.Fatalf(err.Error())
	}
	defer os.RemoveAll(workdir)

	err = os.Chdir(workdir)
	if err != nil {
		t.Fatalf(err.Error())
	}

	hwaf, err := newlogger("hwaf.log")
	if err != nil {
		t.Fatalf(err.Error())
	}
	defer hwaf.Close()

	for _, cmd := range [][]string{
		{"hwaf", "init", "-v=1", "."},
		{"hwaf", "setup", "-v=1"},
		{"hwaf", "pkg", "create", "-script=py", "-v=1", "mypkg"},
		{"hwaf", "pkg", "ls"},
	} {
		err := hwaf.Run(cmd[0], cmd[1:]...)
		if err != nil {
			hwaf.Display()
			t.Fatalf("cmd %v failed: %v", cmd, err)
		}
	}

	mypkgdir := filepath.Join("src", "mypkg")

	// create src/mytools/mypkg/hscript.py file
	ff, err := os.Create(filepath.Join(mypkgdir, "hscript.py"))
	if err != nil {
		t.Fatalf(err.Error())
	}
	_, err = ff.WriteString(
		`
# -*- python -*-
# automatically generated hscript

import waflib.Logs as msg

PACKAGE = {
    'name': 'mypkg',
    'author': ["Sebastien Binet"], 
}

def pkg_deps(ctx):
    # put your package dependencies here.
    # e.g.:
    # ctx.use_pkg('AtlasPolicy')
    return

def options(ctx):
    ctx.load('find_boost')

def configure(ctx):
    ctx.load('find_python')
    ctx.load('find_boost')
    ctx.find_boost(lib='')
    ctx.start_msg("was Boost found ?")
    ctx.end_msg(ctx.env.HWAF_FOUND_BOOST)
    if ctx.env.HWAF_FOUND_BOOST:
        ctx.start_msg("boost version")
        ctx.end_msg(ctx.env.BOOST_VERSION)
    else:
        msg.fatal("Boost could not be found")

def build(ctx):
    return

`)
	if err != nil {
		t.Fatalf(err.Error())
	}

	ff.Sync()
	ff.Close()

	for _, cmd := range [][]string{
		{"hwaf", "configure", "--boost-libs=/bar"},
		{"hwaf"},
	} {
		err := hwaf.Run(cmd[0], cmd[1:]...)
		if err != nil {
			hwaf.Display()
			cfglog := filepath.Join(workdir, "__build__", "config.log")
			cfg, err2 := os.Open(cfglog)
			if err2 == nil {
				defer cfg.Close()
				io.Copy(os.Stderr, cfg)
			}
			t.Fatalf("cmd %v failed: %v", cmd, err)
		}
	}

}

func TestHwafBoostTestPkg(t *testing.T) {
	if testing.Short() {
		t.Skip("skipping test in short mode. (needs CERN-ROOT)")
	}

	workdir, err := ioutil.TempDir("", "hwaf-test-")
	if err != nil {
		t.Fatalf(err.Error())
	}
	defer os.RemoveAll(workdir)

	err = os.Chdir(workdir)
	if err != nil {
		t.Fatalf(err.Error())
	}

	hwaf, err := newlogger("hwaf.log")
	if err != nil {
		t.Fatalf(err.Error())
	}
	defer hwaf.Close()

	for _, cmd := range [][]string{
		{"hwaf", "init", "-v=1", "."},
		{"hwaf", "setup", "-v=1"},
		{"hwaf", "pkg", "co", "git://github.com/hwaf/hwaf-tests-pkg-settings", "pkg-settings"},
		{"hwaf", "pkg", "co", "git://github.com/hwaf/hwaf-tests-boost-tests", "boost-tests"},
		{"hwaf", "pkg", "ls"},
		{"hwaf", "configure"},
		{"hwaf"},
		{"hwaf", "run", "test-hwaf-boost-filesystem.exe", "wscript"},
	} {
		err := hwaf.Run(cmd[0], cmd[1:]...)
		if err != nil {
			hwaf.Display()
			t.Fatalf("cmd %v failed: %v", cmd, err)
		}
	}

	os.RemoveAll("__build__")

	for _, cmd := range [][]string{
		{"hwaf", "configure", "--with-boost=/boo"},
		{"hwaf"},
		{"hwaf", "run", "test-hwaf-boost-filesystem.exe", "wscript"},
	} {
		err := hwaf.Run(cmd[0], cmd[1:]...)
		if err != nil {
			hwaf.Display()
			t.Fatalf("cmd %v failed: %v", cmd, err)
		}
	}

}

// EOF
