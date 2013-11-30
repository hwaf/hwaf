package asetup

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"sort"
	"strings"

	"github.com/gonuts/commander"
	gocfg "github.com/gonuts/config"
	"github.com/hwaf/hwaf/hwaflib"
	"github.com/hwaf/hwaf/platform"
)

func path_exists(name string) bool {
	_, err := os.Stat(name)
	if err == nil {
		return true
	}
	if os.IsNotExist(err) {
		return false
	}
	return false
}

type asetup_t struct {
	ctx     *hwaflib.Context
	cmd     *commander.Command
	args    []string
	opts    options
	verbose bool
}

type options struct {
	projdir   string
	variant   string
	toolchain map[string]string // entries for the hwaf-toolchain section
	env       map[string]string // entries for the hwaf-env section
}

func new_options() options {
	return options{
		toolchain: make(map[string]string),
		env:       make(map[string]string),
	}
}

func Run(ctx *hwaflib.Context, cmd *commander.Command, args []string) error {
	cfg := asetup_t{
		ctx:     ctx,
		cmd:     cmd,
		args:    args,
		opts:    new_options(),
		verbose: cmd.Flag.Lookup("v").Value.Get().(bool),
	}
	return cfg.run()
}

func (a *asetup_t) run() error {
	var err error

	n := "hwaf-" + a.cmd.Name()

	if len(a.args) == 0 {
		if a.verbose {
			a.ctx.Infof("re-using previously asetup'ed workarea...\n")
		}
		// case where we reuse a previously already asetup'ed workarea
		_, err = a.ctx.LocalCfg()
		if err == nil {
			if a.verbose {
				a.ctx.Infof("re-using previously asetup'ed workarea... [done]\n")
			}
			return nil
		}
		err = fmt.Errorf("%v\n'hwaf asetup' called with no argument in a pristine workarea is NOT valid.", err)
		if err != nil {
			return err
		}
	}

	args := make([]string, 0, len(a.args))
	for _, arg := range a.args {
		subarg := strings.Split(arg, ",")
		for _, sarg := range subarg {
			if sarg != "" {
				args = append(args, sarg)
			}
		}
	}

	dirname, err := os.Getwd()
	if err != nil {
		return err
	}

	dirname, err = filepath.Abs(dirname)
	if err != nil {
		return err
	}

	// make sure 'hwaf init' was run at least once in this directory...
	for _, dir := range []string{
		filepath.Join(dirname, ".hwaf", "bin"),
		filepath.Join(dirname, ".hwaf", "tools"),
	} {
		err = os.RemoveAll(dir)
		if err != nil {
			return err
		}
	}
	{
		sub := exec.Command("hwaf", "init", fmt.Sprintf("-v=%v", a.verbose), dirname)
		sub.Stdin = os.Stdin
		sub.Stdout = os.Stdout
		sub.Stderr = os.Stderr
		err = sub.Run()
		if err != nil {
			return err
		}
	}

	err = a.process(args)
	if err != nil {
		return err
	}

	if a.verbose {
		fmt.Printf("%s: asetup workarea [%s]...\n", n, dirname)
		fmt.Printf("%s: projects=%v\n", n, a.opts.projdir)
		// if cfg_fname != "" {
		// 	fmt.Printf("%s: cfg-file=%s\n", n, cfg_fname)
		// }
	}

	subcmd := exec.Command(
		"hwaf", "setup",
		fmt.Sprintf("-v=%v", a.verbose),
		"-p", a.opts.projdir,
	)
	subcmd.Stdin = os.Stdin
	subcmd.Stdout = os.Stdout
	subcmd.Stderr = os.Stderr
	err = subcmd.Run()
	if err != nil {
		return err
	}

	lcfg_fname := "local.conf"
	if !path_exists(lcfg_fname) {
		err = fmt.Errorf("%s: no such file [%s]", n, lcfg_fname)
		if err != nil {
			return err
		}
	}

	lcfg, err := gocfg.ReadDefault(lcfg_fname)
	if err != nil {
		return err
	}

	err = a.handle_toolchain_section(lcfg, lcfg_fname)
	if err != nil {
		return err
	}

	err = a.handle_env_section(lcfg, lcfg_fname, dirname)
	if err != nil {
		return err
	}

	err = lcfg.WriteFile(lcfg_fname, 0600, "")
	if err != nil {
		return err
	}

	if a.verbose {
		fmt.Printf("%s: asetup workarea [%s]... [ok]\n", n, dirname)
	}
	return err
}

func infer_version(arg, projname string, version *string) bool {
	ok := false
	proj_table := map[string]string{
		"mana": "",
		"lcg":  "LCG_",
		"tdaq": "tdaq-common-",
	}
	prefix, haskey := proj_table[projname]
	if !haskey {
		return false
	}
	for _, p := range []string{
		"0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
	} {
		if strings.HasPrefix(arg, prefix+p) {
			*version = arg
			return true
		}
	}
	return ok
}

// FIXME: this should be more thought out... and structured!
func (a *asetup_t) process(args []string) error {
	var err error
	opts := new_options()

	pinfos, err := platform.Infos()
	if err != nil {
		return err
	}

	//cfg_fname := a.cmd.Flag.Lookup("cfg").Value.Get().(string)
	cli_variant := a.cmd.Flag.Lookup("variant").Value.Get().(string)
	cli_arch := a.cmd.Flag.Lookup("arch").Value.Get().(string)
	cli_comp := a.cmd.Flag.Lookup("comp").Value.Get().(string)
	cli_os := a.cmd.Flag.Lookup("os").Value.Get().(string)
	cli_type := a.cmd.Flag.Lookup("type").Value.Get().(string)

	unprocessed := make([]string, 0, len(args))
	projname := "mana-core"
	version := ""
	hwaf_os := pinfos.DistId()
	// fold slX into slcX (ie: all Scientific Linuces are SLCs)
	if pinfos.DistName == "sl" {
		rel := strings.Split(pinfos.DistVers, ".")
		major := rel[0]
		hwaf_os = "slc" + major
	}
	hwaf_comp := "gcc"
	hwaf_arch := ""
	switch runtime.GOARCH {
	case "amd64":
		hwaf_arch = "x86_64"
	case "386":
		hwaf_arch = "i686"
	default:
		//hwaf_arch = "unknown"
		panic(fmt.Sprintf("unknown architecture [%s]", hwaf_arch))
	}
	hwaf_bld := "opt"
	for _, arg := range args {
		has_prefix := func(prefix ...string) bool {
			for _, p := range prefix {
				ok := strings.HasPrefix(arg, p)
				if ok {
					return ok
				}
			}
			return false
		}
		switch arg {
		case "32b":
			hwaf_arch = "i686"
		case "64b":
			hwaf_arch = "x86_64"
		case "opt":
			hwaf_bld = "opt"
		case "dbg":
			hwaf_bld = "dbg"
		case "mana", "mana-core":
			projname = "mana-core"
		case "mana-ext", "lcg":
			projname = arg
		case "tdaq", "tdaq-common":
			projname = "tdaq-common"
		default:
			if has_prefix(
				"2012", "2013",
				"0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
			) {
				version = arg
			} else if has_prefix("gcc") || has_prefix("clang") {
				hwaf_comp = arg
			} else if infer_version(arg, projname, &version) {
				//version = version
			} else {
				unprocessed = append(unprocessed, arg)
			}
		}
	}
	if len(unprocessed) > 0 {
		err = fmt.Errorf("unprocessed asetup options: %v", unprocessed)
	}

	// honour CLI args
	for _, v := range [][]*string{
		{&cli_arch, &hwaf_arch},
		{&cli_os, &hwaf_os},
		{&cli_comp, &hwaf_comp},
		{&cli_type, &hwaf_bld},
	} {
		if *v[0] != "" {
			*v[1] = *v[0]
		}
	}

	sitedir := a.ctx.Sitedir()
	if sitedir == "" {
		sitedir = filepath.Join("", "opt", "sw", "atlas")
		a.ctx.Warnf("no $HWAF_SITEDIR env. variable. will use [%s]\n", sitedir)
	}

	if a.verbose {
		a.ctx.Infof("using sitedir: [%s]\n", sitedir)
	}

	if !path_exists(sitedir) {
		err = fmt.Errorf("no such directory [%s]", sitedir)
		return err
	}

	usr_variant := fmt.Sprintf("%s-%s-%s-%s", hwaf_arch, hwaf_os, hwaf_comp, hwaf_bld)
	proj_root := filepath.Join(sitedir, projname)
	if !path_exists(proj_root) {
		err = fmt.Errorf("no such directory [%s]", proj_root)
		return err
	}

	if a.verbose {
		a.ctx.Infof("using project root [%s]\n", proj_root)
	}

	if version == "" {
		// get the latest one.
		var versions []string
		versions, err = filepath.Glob(filepath.Join(proj_root, "*"))
		if err != nil {
			return err
		}
		sort.Strings(versions)
		version = versions[len(versions)-1]
		version, _ = filepath.Abs(version)
		version = filepath.Base(version)
	}
	opts.projdir = filepath.Join(proj_root, version)
	if !path_exists(opts.projdir) {
		err = fmt.Errorf("no such directory [%s]", opts.projdir)
		return err
	}

	if a.verbose {
		a.ctx.Infof("using project dir [%s]\n", opts.projdir)
	}

	// dft_variant is a variation on DefaultVariant.
	dft_variant := fmt.Sprintf(
		"%s-%s-%s-%s",
		hwaf_arch,
		hwaf_os,
		strings.Split(a.ctx.DefaultVariant(), "-")[2], // compiler
		hwaf_bld,
	)

	found := false
	for ii, variant := range []string{
		cli_variant,
		usr_variant,
		a.ctx.Variant(),
		a.ctx.DefaultVariant(),
		dft_variant,
	} {
		if variant == "" {
			continue
		}
		dir := filepath.Join(opts.projdir, variant)
		if a.verbose {
			fmt.Printf("---> (%03d) [%s]... ", ii, dir)
		}
		if !path_exists(dir) {
			if a.verbose {
				fmt.Printf("[err]\n")
			}
			continue
		}
		opts.projdir = dir
		opts.variant = variant
		if a.verbose {
			fmt.Printf("[ok]\n")
		}
		found = true
		break
	}
	if !found {
		return fmt.Errorf("hwaf: could not find a suitable project")
	}
	a.opts = opts
	return err
}

func (a *asetup_t) handle_toolchain_section(lcfg *gocfg.Config, lcfg_fname string) error {
	var err error
	n := "hwaf-" + a.cmd.Name()

	section := "hwaf-toolchain"
	if !lcfg.HasSection(section) {
		if !lcfg.AddSection(section) {
			err = fmt.Errorf("%s: could not create section [%s] in file [%s]",
				n, section, lcfg_fname)
			if err != nil {
				return err
			}
		}
	}
	for k, v := range a.opts.toolchain {
		if lcfg.HasOption(section, k) {
			lcfg.RemoveOption(section, k)
		}
		ok := lcfg.AddOption(section, k, v)
		if !ok {
			err = fmt.Errorf(
				"%s: could not add option [%s=%q] to file [%s]",
				n, k, v, lcfg_fname,
			)
			if err != nil {
				return err
			}
		}
	}
	return err
}

func (a *asetup_t) handle_env_section(lcfg *gocfg.Config, lcfg_fname, dirname string) error {
	var err error
	n := "hwaf-" + a.cmd.Name()

	section := "hwaf-env"
	if !lcfg.HasSection(section) {
		if !lcfg.AddSection(section) {
			err = fmt.Errorf("%s: could not create section [%s] in file [%s]",
				n, section, lcfg_fname)
			if err != nil {
				return err
			}
		}
	}
	// add a few asetup defaults...
	for k, v := range map[string]string{
		"SVNGROUPS": "svn+ssh://svn.cern.ch/reps/atlasgroups",
		"SVNGRP":    "svn+ssh://svn.cern.ch/reps/atlasgrp",
		"SVNINST":   "svn+ssh://svn.cern.ch/reps/atlasinst",
		"SVNOFF":    "svn+ssh://svn.cern.ch/reps/atlasoff",
		"SVNPERF":   "svn+ssh://svn.cern.ch/reps/atlasperf",
		"SVNPHYS":   "svn+ssh://svn.cern.ch/reps/atlasphys",
		"SVNROOT":   "svn+ssh://svn.cern.ch/reps/atlasoff",
		"SVNUSR":    "svn+ssh://svn.cern.ch/reps/atlasusr",
		"TestArea":  dirname,
	} {
		a.opts.env[k] = v
	}

	for k, v := range a.opts.env {
		if lcfg.HasOption(section, k) {
			lcfg.RemoveOption(section, k)
		}
		ok := lcfg.AddOption(section, k, v)
		if !ok {
			err = fmt.Errorf(
				"%s: could not add option [%s=%q] to file [%s]",
				n, k, v, lcfg_fname,
			)
			if err != nil {
				return err
			}
		}
	}

	return err
}

// EOF
