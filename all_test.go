package main_test

import (
	"fmt"
	"io"
	"io/ioutil"
	"os"
	"os/exec"
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
		cargs := make([]interface{}, 1, len(args)+1)
		cargs[0] = bin
		for _, arg := range args {
			cargs = append(cargs, arg)
		}
		cmd_line = fmt.Sprintf("%v", cargs...)
	}
	cmd.cmds = append(cmd.cmds, cmd_line)
	c := exec.Command(bin, args...)
	c.Stdout = cmd.f
	c.Stderr = cmd.f
	_, err := cmd.f.WriteString("## " + cmd_line + "\n")
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

// EOF
