package main

import (
	"fmt"
	"io"
	"io/ioutil"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"time"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
	"github.com/hwaf/gas"
)

func hwaf_make_cmd_self_bdist() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_self_bdist,
		UsageLine: "bdist [options]",
		Short:     "create a binary distribution of hwaf itself",
		Long: `
self bdist creates a binary distribution of hwaf itself.

ex:
 $ hwaf self bdist
 $ hwaf self bdist -version=20130101
`,
		Flag: *flag.NewFlagSet("hwaf-self-bdist", flag.ExitOnError),
	}
	cmd.Flag.Bool("q", true, "only print error and warning messages, all other output will be suppressed")
	cmd.Flag.String("version", "", "version of the binary distribution (default: 'time now')")

	return cmd
}

func hwaf_run_cmd_self_bdist(cmd *commander.Command, args []string) {
	var err error

	n := "hwaf-self-" + cmd.Name()

	switch len(args) {
	case 0:
		// ok
	default:
		err = fmt.Errorf("%s: does NOT take any argument", n)
		handle_err(err)
	}

	quiet := cmd.Flag.Lookup("q").Value.Get().(bool)

	bdist_name := "hwaf"
	bdist_vers := cmd.Flag.Lookup("version").Value.Get().(string)
	bdist_cmtcfg := fmt.Sprintf("%s-%s", runtime.GOOS, runtime.GOARCH)

	if bdist_vers == "" {
		bdist_vers = time.Now().Format("20060102")
	}

	dirname := fmt.Sprintf("%s-%s-%s", bdist_name, bdist_vers, bdist_cmtcfg)
	fname := dirname + ".tar.gz"

	if !quiet {
		fmt.Printf("%s [%s]...\n", n, fname)
	}

	tmpdir, err := ioutil.TempDir("", "hwaf-self-bdist-")
	handle_err(err)
	defer os.RemoveAll(tmpdir)
	//fmt.Printf(">>> [%s]\n", tmpdir)

	//
	top := filepath.Join(tmpdir, dirname)
	// create hierarchy of dirs for bdist
	for _, dir := range []string{
		"bin",
		"share",
		filepath.Join("share", "hwaf"),
	} {
		err = os.MkdirAll(filepath.Join(top, dir), 0755)
		handle_err(err)
	}

	// add hep-waftools cache
	hwaf_dir, err := gas.Abs("github.com/hwaf/hwaf")
	handle_err(err)

	src_hwaf_tools := filepath.Join(hwaf_dir, "py-hwaftools")
	hwaf_tools := filepath.Join(top, "share", "hwaf", "tools")

	err = copytree(hwaf_tools, src_hwaf_tools)
	handle_err(err)

	// remove git stuff
	err = os.RemoveAll(filepath.Join(hwaf_tools, ".git"))
	handle_err(err)

	// add share/hwaf/hwaf.conf
	err = ioutil.WriteFile(
		filepath.Join(top, "share", "hwaf", "hwaf.conf"),
		[]byte(`# hwaf config file
[hwaf]

## EOF ##
`),
		0644,
	)
	handle_err(err)

	// temporary GOPATH - install go-deps
	gopath := filepath.Join(tmpdir, "gocode")
	err = os.MkdirAll(gopath, 0755)
	handle_err(err)

	orig_gopath := os.Getenv("GOPATH")
	err = os.Setenv("GOPATH", gopath)
	handle_err(err)
	defer os.Setenv("GOPATH", orig_gopath)

	for _, gopkg := range []string{
		"github.com/hwaf/hwaf",
		"github.com/hwaf/git-tools/git-archive-all",
		"github.com/hwaf/git-tools/git-rm-submodule",
		"github.com/hwaf/git-tools/git-check-clean",
		"github.com/hwaf/git-tools/git-check-non-tracking",
		"github.com/hwaf/git-tools/git-check-unpushed",
	} {
		goget := exec.Command("go", "get", "-v", gopkg)
		goget.Dir = gopath
		if !quiet {
			goget.Stdout = os.Stdout
			goget.Stderr = os.Stderr
		}
		err = goget.Run()
		handle_err(err)

		// install under /bin
		dst_fname := filepath.Join(top, "bin", filepath.Base(gopkg))
		dst, err := os.OpenFile(dst_fname, os.O_WRONLY|os.O_CREATE, 0755)
		handle_err(err)
		defer func(dst *os.File) {
			err := dst.Sync()
			handle_err(err)
			err = dst.Close()
			handle_err(err)
		}(dst)

		src_fname := filepath.Join(gopath, "bin", filepath.Base(gopkg))
		if !path_exists(src_fname) {
			// maybe a cross-compilation ?
			src_fname = filepath.Join(gopath, "bin", runtime.GOOS+"_"+runtime.GOARCH, filepath.Base(gopkg))
		}
		src, err := os.Open(src_fname)
		handle_err(err)
		defer func(src *os.File) {
			err := src.Close()
			handle_err(err)
		}(src)

		_, err = io.Copy(dst, src)
		handle_err(err)
	}

	// add waf-bin
	waf_fname := filepath.Join(top, "bin", "waf")
	if path_exists(waf_fname) {
		err = os.Remove(waf_fname)
		handle_err(err)
	}
	waf_dst, err := os.OpenFile(waf_fname, os.O_WRONLY|os.O_CREATE, 0777)
	handle_err(err)
	defer func() {
		err = waf_dst.Sync()
		handle_err(err)
		err = waf_dst.Close()
		handle_err(err)
	}()

	waf_src, err := os.Open(filepath.Join(
		gopath, "src", "github.com", "hwaf", "hwaf", "waf"),
	)
	handle_err(err)
	defer waf_src.Close()
	_, err = io.Copy(waf_dst, waf_src)
	handle_err(err)

	pwd, err := os.Getwd()
	handle_err(err)

	// package everything up
	err = _tar_gz(filepath.Join(pwd, fname), top)
	handle_err(err)

	if !quiet {
		fmt.Printf("%s [%s]... [ok]\n", n, fname)
	}
}

// EOF
