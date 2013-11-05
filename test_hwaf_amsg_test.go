//+build amsg_build

package main_test

import (
	"io/ioutil"
	"os"
	"testing"
)

func TestAmsgBuild(t *testing.T) {

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

	err = hwaf.Run("git", "clone", "git://github.com/mana-fwk/amsg-build")
	if err != nil {
		t.Fatalf(err.Error())
	}

	err = os.Chdir("amsg-build")
	if err != nil {
		t.Fatalf(err.Error())
	}

	err = hwaf.Run("/bin/sh", "build.sh")
	if err != nil {
		t.Fatalf(err.Error())
	}
}
