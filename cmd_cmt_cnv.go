package main

import (
	"bytes"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
)

func hwaf_make_cmd_cmt_cnv() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_cmt_cnv,
		UsageLine: "cmt-cnv [options] <req-file>",
		Short:     "convert a CMT req-file into a hwaf script",
		Long: `
cmt-cnv converts a CMT req-file into a hwaf script.

ex:
 $ hwaf cmt-cnv ./cmt/requirements
`,
		Flag: *flag.NewFlagSet("hwaf-cmt-cnv", flag.ExitOnError),
		//CustomFlags: true,
	}
	cmd.Flag.Bool("q", true, "only print error and warning messages, all other output will be suppressed")
	return cmd
}

func hwaf_run_cmd_cmt_cnv(cmd *commander.Command, args []string) {
	var err error
	n := "hwaf-" + cmd.Name()

	reqfile := ""
	switch len(args) {
	case 1:
		reqfile = args[0]
	default:
		err = fmt.Errorf("%s: you need to give a cmt/requirements file to convert", n)
		handle_err(err)
	}

	reqfile = os.ExpandEnv(reqfile)
	reqfile = filepath.Clean(reqfile)

	quiet := cmd.Flag.Lookup("q").Value.Get().(bool)

	if !quiet {
		fmt.Printf("%s: converting [%s]...\n", n, reqfile)
	}

	if !path_exists(reqfile) {
		err = fmt.Errorf("no such file [%s]", reqfile)
		handle_err(err)
	}

	cmt_dir := filepath.Dir(reqfile)
	cmt_pkgfullname, err := func() (string, error) {
		workdir, err := g_ctx.Workarea()
		if err != nil {
			return "", err
		}

		cfg, err := g_ctx.LocalCfg()
		if err != nil {
			return "", err
		}

		pkgdir := "src"
		if cfg.HasOption("hwaf-cfg", "cmtpkgs") {
			pkgdir, err = cfg.String("hwaf-cfg", "cmtpkgs")
			if err != nil {
				return "", err
			}
		}
		basepath := filepath.Join(workdir, pkgdir)
		return filepath.Rel(basepath, filepath.Base(cmt_dir))
	}()
	handle_err(err)

	err = os.Chdir(cmt_dir)
	handle_err(err)

	cmt_pkgname := filepath.Base(cmt_pkgfullname)

	cmt_installarea := os.Getenv("CMTINSTALLAREA")
	if cmt_installarea == "" {
		err = fmt.Errorf("no $CMTINSTALLAREA env.var.")
		handle_err(err)
	}

	if !path_exists(cmt_installarea) {
		err = fmt.Errorf("no such directory [%s]", cmt_installarea)
		handle_err(err)
	}

	cmt_installarea_inc := filepath.Join(cmt_installarea, "include")
	if !path_exists(cmt_installarea_inc) {
		err = fmt.Errorf("no such directory [%s]", cmt_installarea_inc)
		handle_err(err)
	}

	cmt_show := func(cmtargs ...string) ([]string, error) {
		cmdargs := append([]string{"show"}, cmtargs...)
		cmt := exec.Command("cmt", cmdargs...)
		cmt.Dir = cmt_dir
		bout, err := cmt.Output()
		if err != nil {
			return nil, err
		}
		lines := make([]string, 0, 2)
		for _, line := range bytes.Split(bout, []byte("\n")) {
			sline := strings.Trim(string(line), "\t\r\n")
			lines = append(lines, sline)
		}
		return lines, nil
	}

	pkg_libs := make(map[string][]string)
	get_libs := func(libname string) ([]string, error) {
		if libs, ok := pkg_libs[libname]; ok {
			return libs, nil
		}
		libs := []string{}
		for _, cmdargs := range [][]string{
			[]string{"macro_value", fmt.Sprintf("%s_use_linkopts", libname)},
			[]string{"macro_value", fmt.Sprintf("%slinkopts", libname)},
		} {
			raw_libs, err := cmt_show(cmdargs...)
			if err != nil {
				return nil, err
			}
			for _, raw_lib := range raw_libs {
				if !strings.HasPrefix(raw_lib, "-l") {
					continue
				}
				lib := strings.Trim(raw_lib[2:len(raw_lib)-1], " \t\r\n")
				if lib != libname {
					libs = append(libs, lib)
				}
			}
		}
		if !quiet {
			fmt.Printf(" +lib[%s]: %v\n", libname, libs)
		}
		pkg_libs[libname] = libs
		return libs, nil
	}

	pkg_deps := make(map[string][]string)
	get_deps := func(libname string) ([]string, error) {
		if deps, ok := pkg_deps[libname]; ok {
			return deps, nil
		}
		deps := []string{}
		raw_deps, err := cmt_show("macro_value", fmt.Sprintf("%s_dependencies", libname))
		if err != nil {
			return nil, err
		}
		for _, raw_dep := range raw_deps {
			raw_dep = strings.Trim(raw_dep, " \t\r\n")
			if strings.HasPrefix(raw_dep, "#CMT") {
				continue
			}
			if strings.HasPrefix(raw_dep, "install_includes") {
				continue
			}
			if !quiet {
				fmt.Printf(" +dep: %s\n", raw_dep)
			}
			if !sort.StringsAreSorted(deps) {
				sort.Strings(deps)
			}
			idx := sort.SearchStrings(deps, raw_dep)
			if !(idx < len(deps) && deps[idx] == raw_dep) {
				deps = append(deps, raw_dep)
			}
		}
		pkg_deps[libname] = deps
		return deps, nil
	}

	pkg_root, err := func() (string, error) {
		out, err := cmt_show("macro_value", fmt.Sprintf("%s_root", cmt_pkgname))
		if err != nil {
			return "", err
		}
		return strings.Trim(out[0], " \t\r\n"), nil
	}()
	handle_err(err)

	if !quiet {
		fmt.Printf("%s: pkg-root: %s\n", n, pkg_root)
	}

	constituents, err := cmt_show("constituents")
	handle_err(err)
	if !quiet {
		fmt.Printf("%s: constituents=%v\n", n, constituents)
	}

	// hack!!! FIXME!!!
	if false {
		get_libs("foo")
		get_deps("foo")
	}

	handle_err(err)
	if !quiet {
		fmt.Printf("%s: converting [%s]... [ok]\n", n, reqfile)
	}
}

// EOF
