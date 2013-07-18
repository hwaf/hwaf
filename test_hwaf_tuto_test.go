package main_test

import (
	"io/ioutil"
	"os"
	"path/filepath"
	"testing"
)

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

func TestHwafTutoHscript(t *testing.T) {
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
		{"/bin/rm", "-f", "src/mytools/mypkg/wscript"},
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
	ff, err := os.Create(filepath.Join(mypkgdir, "hscript.yml"))
	if err != nil {
		t.Fatalf(err.Error())
	}
	_, err = ff.WriteString(
		`
# -*- yml -*-

package: {
    name: mytools/mypkg,
    authors: "Sebastien Binet",
    deps: {
        public: [],
    },
}

options: {}
configure: {
    tools: [find_clhep, find_python],
    env: {
        PYTHONPATH: "${INSTALL_AREA}/python:${PYTHONPATH}",
    },
}

build: {

    cxx-hello-world: {
        features: "cxx cxxshlib",
        source:   "src/mypkgtool.cxx",
        target:   "hello-world",
    },

    py-hello: {
        features: "py",
        source:   [python/pyhello.py, python/__init__.py],
        install_path: "${INSTALL_AREA}/python/mypkg",
        use:          "cxx-hello-world",
    },
}
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

func TestHwafHepTuto(t *testing.T) {
	if testing.Short() {
		t.Skip("skipping test in short mode.")
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
		{"hwaf", "init", "-q=0", "."},
		{"hwaf", "setup", "-q=0"},
		{"hwaf", "pkg", "co", "git://github.com/hwaf/hwaf-tests-pkg-settings", "pkg-settings"},
		{"hwaf", "pkg", "co", "git://github.com/hwaf/hwaf-tests-pkg-aa", "pkg-aa"},
		{"hwaf", "pkg", "co", "git://github.com/hwaf/hwaf-tests-pkg-ab", "pkg-ab"},
		{"hwaf", "pkg", "co", "git://github.com/hwaf/hwaf-tests-pkg-ac", "pkg-ac"},
		{"hwaf", "pkg", "ls"},
		{"hwaf", "configure"},
		{"hwaf", "build"},
		{"hwaf", "install"},
		{"hwaf", "run", "python", "-c", "import pkgaa"},
		{"hwaf"},
		{"hwaf", "run", "python", "-c", "import pkgaa"},
		{"hwaf", "bdist"},
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
    ctx.use_pkg('pkg-aa')
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

def build(ctx):
    ctx.build_linklib(
        name = 'hello-clhep',
        source = 'src/*.cxx',
        use = ['CLHEP'],
        )
    
    ctx(
        features     = 'py',
        name         = 'py-clhep',
        source       = 'python/pyclhep.py',
        install_path = '${INSTALL_AREA}/python',
        )

    return

## EOF
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
#include "CLHEP/Vector/LorentzVector.h"

extern "C" {
  
float
clhep_calc_mt(float x, float y, float z, float t) 
{
  return CLHEP::HepLorentzVector(x, y, z, t).mt();
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

	ff, err = os.Create(filepath.Join(mypkgdir, "python", "pyclhep.py"))
	if err != nil {
		t.Fatalf(err.Error())
	}

	_, err = ff.WriteString(`
import ctypes
lib = ctypes.cdll.LoadLibrary('libhello-clhep.so')
if not lib:
    raise RuntimeError("could not find hello-clhep")

calc_mt = lib.clhep_calc_mt
calc_mt.argtypes = [ctypes.c_float]*4
calc_mt.restype = ctypes.c_float

import sys
sys.stdout.write("hlv.mt(10,10,10,20) = %s\n" % calc_mt(10,10,10,20))
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
		{"hwaf", "run", "python", "-c", "import pyclhep"},
		{"hwaf", "show", "projects"},
		{"hwaf", "show", "pkg-uses", "mytools/mypkg"},
		{"hwaf", "show", "flags", "CXXFLAGS", "LINKFLAGS"},
		{"hwaf", "show", "constituents"},
	} {
		err := hwaf.Run(cmd[0], cmd[1:]...)
		if err != nil {
			hwaf.Display()
			t.Fatalf("cmd %v failed: %v", cmd, err)
		}
	}

	// testing reflex dict...
	err = os.MkdirAll(filepath.Join(mypkgdir, "mypkg"), 0777)
	if err != nil {
		t.Fatalf(err.Error())
	}

	ff, err = os.Create(filepath.Join(mypkgdir, "mypkg", "hlv.hh"))
	if err != nil {
		t.Fatalf(err.Error())
	}

	_, err = ff.WriteString(`
#ifndef MYPKG_HLV_HH
#define MYPKG_HLV_HH 1

#include "CLHEP/Vector/LorentzVector.h"

class MyHlv 
{
  CLHEP::HepLorentzVector m_hlv;

public:
  CLHEP::HepLorentzVector& hlv();
};

#endif /* !MYPKG_HLV_HH */
`)
	if err != nil {
		t.Fatalf(err.Error())
	}
	ff.Sync()
	ff.Close()

	ff, err = os.Create(filepath.Join(mypkgdir, "mypkg", "selection.xml"))
	if err != nil {
		t.Fatalf(err.Error())
	}

	_, err = ff.WriteString(`
<!-- src/mytools/mypkg/mypkg/selection.xml -->
<lcgdict>
  <class name="MyHlv" />
  <class name="CLHEP::HepLorentzVector" />
</lcgdict>
`)
	if err != nil {
		t.Fatalf(err.Error())
	}
	ff.Sync()
	ff.Close()

	ff, err = os.Create(filepath.Join(mypkgdir, "mypkg", "mypkgdict.h"))
	if err != nil {
		t.Fatalf(err.Error())
	}

	_, err = ff.WriteString(`
#ifndef MYPKG_MYPKGDICT_H
#define MYPKG_MYPKGDICT_H 1

#include "mypkg/hlv.hh"

namespace mypkgdict {
  struct tmp {
    MyHlv m_1;
  };
}
#endif
`)
	if err != nil {
		t.Fatalf(err.Error())
	}
	ff.Sync()
	ff.Close()

	ff, err = os.Create(filepath.Join(mypkgdir, "src", "hlv.cxx"))
	if err != nil {
		t.Fatalf(err.Error())
	}

	_, err = ff.WriteString(`
#include "mypkg/hlv.hh"

CLHEP::HepLorentzVector&
MyHlv::hlv()
{
  return m_hlv;
}
`)
	if err != nil {
		t.Fatalf(err.Error())
	}
	ff.Sync()
	ff.Close()

	ff, err = os.Create(filepath.Join(mypkgdir, "wscript"))
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
    ctx.use_pkg('pkg-aa')
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

def build(ctx):
    ctx.build_linklib(
        name = 'hello-clhep',
        source = 'src/*.cxx',
        use = ['CLHEP'],
        )
    
    ctx.build_reflex_dict(
        name     = 'mypkg',
        source   = 'mypkg/mypkgdict.h',
        selection_file = 'mypkg/selection.xml',
        use      = ['hello-clhep', 'Reflex',],
        )

    ctx(
        features     = 'py',
        name         = 'py-clhep',
        source       = 'python/pyclhep.py',
        install_path = '${INSTALL_AREA}/python',
        )

    return

## EOF
`)
	if err != nil {
		t.Fatalf(err.Error())
	}

	ff.Sync()
	ff.Close()

	for _, cmd := range [][]string{
		{"hwaf"},
		{"hwaf", "run", "python2", "-c", "import pyclhep"},
		{"hwaf", "run", "python2", "-c", "import PyCintex, ROOT; h = ROOT.MyHlv(); h.hlv().px()"},
	} {
		err := hwaf.Run(cmd[0], cmd[1:]...)
		if err != nil {
			hwaf.Display()
			t.Fatalf("cmd %v failed: %v", cmd, err)
		}
	}
}

// EOF
