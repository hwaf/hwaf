package main_test

import (
	"io"
	"io/ioutil"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
)

type logcmd struct {
	f    *os.File
	cmds []string
}

func newlogger(fname string) (*logcmd, error) {
	f, err := os.Create(fname)
	if err != nil {
		return nil, err
	}
	return &logcmd{f: f, cmds: nil}, nil
}

func (cmd *logcmd) LastCmd() string {
	if len(cmd.cmds) <= 0 {
		return ""
	}
	return cmd.cmds[len(cmd.cmds)-1]
}
func (cmd *logcmd) Run(bin string, args ...string) error {
	cmd_line := ""
	{
		cargs := make([]string, 1, len(args)+1)
		cargs[0] = bin
		cargs = append(cargs, args...)
		cmd_line = strings.Join(cargs, " ")
	}
	cmd.cmds = append(cmd.cmds, cmd_line)
	c := exec.Command(bin, args...)
	c.Stdout = cmd.f
	c.Stderr = cmd.f

	_, err := cmd.f.WriteString("\n" + strings.Repeat("#", 80) + "\n")
	if err != nil {
		return err
	}

	_, err = cmd.f.WriteString("## " + cmd_line + "\n")
	if err != nil {
		return err
	}

	return c.Run()
}

func (cmd *logcmd) Close() error {
	return cmd.f.Close()
}

func (cmd *logcmd) Display() {
	cmd.f.Seek(0, 0)
	io.Copy(os.Stderr, cmd.f)
}

func TestBasicSetup(t *testing.T) {
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
		{"hwaf", "init", "-q=0", "."},
		{"hwaf", "setup", "-q=0"},
		{"hwaf", "configure"},
		{"hwaf", "build"},
		{"hwaf", "install"},
	} {
		err := hwaf.Run(cmd[0], cmd[1:]...)
		if err != nil {
			hwaf.Display()
			t.Fatalf("cmd %v failed: %v", cmd, err)
		}
	}

}

func TestBasicState(t *testing.T) {
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

	err = hwaf.Run("hwaf", "init", "-q=0", ".")
	if err != nil {
		hwaf.Display()
		t.Fatalf("cmd %v failed: %v", hwaf.LastCmd(), err)
	}

	err = hwaf.Run("hwaf", "-q=0")
	if err == nil {
		hwaf.Display()
		t.Fatalf("cmd %v should have failed!", hwaf.LastCmd())
	}

	err = hwaf.Run("hwaf", "setup", "-q=0", ".")
	if err != nil {
		hwaf.Display()
		t.Fatalf("cmd %v failed: %v", hwaf.LastCmd(), err)
	}
}

func TestHwafTuto(t *testing.T) {
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
		{"hwaf", "init", "-q=0", "."},
		{"hwaf", "setup", "-q=0"},
		{"hwaf", "pkg", "create", "-q=0", "mytools/mypkg"},
		{"hwaf", "pkg", "ls"},
	} {
		err := hwaf.Run(cmd[0], cmd[1:]...)
		if err != nil {
			hwaf.Display()
			t.Fatalf("cmd %v failed: %v", cmd, err)
		}
	}

	mypkgdir := filepath.Join("src", "mytools", "mypkg")

	// create src/mytools/mypkg/wscript file
	ff, err := os.Create(filepath.Join(mypkgdir, "wscript"))
	if err != nil {
		t.Fatalf(err.Error())
	}
	_, err = ff.WriteString(
		`
# -*- python -*-
# automatically generated wscript

import waflib.Logs as msg

PACKAGE = {
    'name': 'mytools/mypkg',
    'author': ["Sebastien Binet"], 
}

def pkg_deps(ctx):
    # put your package dependencies here.
    # e.g.:
    # ctx.use_pkg('AtlasPolicy')
    return

def configure(ctx):
    ctx.load('find_clhep')
    ctx.find_clhep(mandatory=False)
    ctx.start_msg("was clhep found ?")
    ctx.end_msg(ctx.env.HWAF_FOUND_CLHEP)
    if ctx.env.HWAF_FOUND_CLHEP:
        ctx.start_msg("clhep version")
        ctx.end_msg(ctx.env.CLHEP_VERSION)
        msg.info("clhep linkflags: %s" % ctx.env['LINKFLAGS_CLHEP'])
        msg.info("clhep cxxflags: %s" % ctx.env['CXXFLAGS_CLHEP'])
    
    from waflib.Utils import subst_vars
    ctx.load('find_python')
    ctx.find_python(mandatory=True)
    ctx.declare_runtime_env('PYTHONPATH') 
    pypath = subst_vars('${INSTALL_AREA}/python', ctx.env)
    ctx.env.prepend_value('PYTHONPATH', [pypath])

def build(ctx):
    ctx(features = 'cxx cxxshlib',
        name     = 'cxx-hello-world',
        source   = 'src/mypkgtool.cxx',
        target   = 'hello-world',
        )

    ctx(features     = 'py',
        name         = 'py-hello',
        source       = 'python/pyhello.py python/__init__.py',
        install_path = '${INSTALL_AREA}/python/mypkg',
        use          = 'cxx-hello-world',
        )
    return

`)
	if err != nil {
		t.Fatalf(err.Error())
	}

	ff.Sync()
	ff.Close()

	ff, err = os.Create(filepath.Join(mypkgdir, "src", "mypkgtool.cxx"))
	if err != nil {
		t.Fatalf(err.Error())
	}
	_, err = ff.WriteString(`
#include <cmath>

extern "C" {
  
float
calc_hypot(float x, float y) 
{
  return std::sqrt(x*x + y*y);
}

}

// EOF
`)
	if err != nil {
		t.Fatalf(err.Error())
	}

	ff.Sync()
	ff.Close()

	err = os.MkdirAll(filepath.Join(mypkgdir, "python"), 0777)
	if err != nil {
		t.Fatalf(err.Error())
	}

	ff, err = os.Create(filepath.Join(mypkgdir, "python", "__init__.py"))
	if err != nil {
		t.Fatalf(err.Error())
	}
	ff.Close()

	ff, err = os.Create(filepath.Join(mypkgdir, "python", "pyhello.py"))
	if err != nil {
		t.Fatalf(err.Error())
	}

	_, err = ff.WriteString(`
import ctypes
lib = ctypes.cdll.LoadLibrary('libhello-world.so')
if not lib:
    raise RuntimeError("could not find hello-world")

calc_hypot = lib.calc_hypot
calc_hypot.argtypes = [ctypes.c_float]*2
calc_hypot.restype = ctypes.c_float

import sys
sys.stdout.write("hypot(10,20) = %s\n" % calc_hypot(10,20))
sys.stdout.flush()
# EOF #
`)
	if err != nil {
		t.Fatalf(err.Error())
	}
	ff.Sync()
	ff.Close()

	for _, cmd := range [][]string{
		{"hwaf", "configure"},
		{"hwaf"},
		{"hwaf", "run", "python", "-c", "import mypkg.pyhello"},
		{"hwaf", "show", "projects"},
		{"hwaf", "show", "pkg-uses", "mytools/mypkg"},
		{"hwaf", "show", "flags", "CXXFLAGS", "LINKFLAGS"},
		{"hwaf", "show", "constituents"},
		{"hwaf", "pkg", "rm", "mytools/mypkg"},
		{"hwaf", "pkg", "ls"},
	} {
		err := hwaf.Run(cmd[0], cmd[1:]...)
		if err != nil {
			hwaf.Display()
			t.Fatalf("cmd %v failed: %v", cmd, err)
		}
	}
}

// EOF
