package main_test

import (
	"io/ioutil"
	"os"
	"path/filepath"
	"testing"
)

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

func TestPkgCoRm(t *testing.T) {
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
		{"hwaf", "pkg", "co", "git://github.com/hwaf/hwaf-tests-pkg-settings", "pkg-settings"},
	} {
		err := hwaf.Run(cmd[0], cmd[1:]...)
		if err != nil {
			hwaf.Display()
			t.Fatalf("cmd %v failed: %v", cmd, err)
		}
	}

	// test adding the same package
	err = hwaf.Run("hwaf", "pkg", "co", "git://github.com/hwaf/hwaf-tests-pkg-settings", "pkg-settings")
	if err == nil {
		t.Fatalf("hwaf pkg co should have FAILED!")
	}

	// test adding a different package under the same name
	err = hwaf.Run("hwaf", "pkg", "co", "git://github.com/hwaf/hwaf-tests-pkg-aa", "pkg-settings")
	if err == nil {
		t.Fatalf("hwaf pkg co should have FAILED!")
	}

	// test adding the same package under a different name
	err = hwaf.Run("hwaf", "pkg", "co", "git://github.com/hwaf/hwaf-tests-pkg-settings", "pkg-settings-new")
	if err != nil {
		t.Fatalf(err.Error())
	}

	// test removing the package "by hand"
	err = os.RemoveAll(filepath.Join(workdir, "src", "pkg-settings"))
	if err != nil {
		t.Fatalf(err.Error())
	}

	err = hwaf.Run("hwaf", "pkg", "rm", "pkg-settings")
	if err == nil {
		t.Fatalf("hwaf pkg rm should have FAILED!")
	}

	// recover
	err = hwaf.Run("hwaf", "pkg", "rm", "-f", "pkg-settings")
	if err != nil {
		t.Fatalf(err.Error())
	}

	// add it back
	err = hwaf.Run("hwaf", "pkg", "co", "git://github.com/hwaf/hwaf-tests-pkg-settings", "pkg-settings")
	if err != nil {
		t.Fatalf(err.Error())
	}
}

// EOF
