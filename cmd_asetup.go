package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"sort"
	"strings"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
	"github.com/mana-fwk/hwaf/platform"
	gocfg "github.com/sbinet/go-config/config"
)

func hwaf_make_cmd_asetup() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_asetup,
		UsageLine: "asetup [options] <args>",
		Short:     "setup a workarea with Athena-like defaults",
		Long: `
asetup sets up a workarea with Athena-like defaults.

ex:
 $ mkdir my-work-area && cd my-work-area
 $ hwaf asetup
 $ hwaf asetup mana,20121207
 $ hwaf asetup mana 20121207
 $ hwaf asetup -arch=64    mana 20121207
 $ hwaf asetup -comp=gcc44 mana 20121207
 $ hwaf asetup -os=centos6 mana 20121207
 $ hwaf asetup -type=opt   mana 20121207
 $ hwaf asetup -cmtcfg=x86_64-slc6-gcc44-opt mana 20121207
 $ CMTCFG=x86_64-slc6-gcc44-opt \
   hwaf asetup mana 20121207
`,
		Flag: *flag.NewFlagSet("hwaf-setup", flag.ExitOnError),
	}
	//cmd.Flag.String("p", "", "List of paths to projects to setup against")
	//cmd.Flag.String("cfg", "", "Path to a configuration file")
	cmd.Flag.Bool("q", true, "only print error and warning messages, all other output will be suppressed")
	cmd.Flag.String("arch", "", "explicit architecture to use (32/64)")
	cmd.Flag.String("comp", "", "explicit compiler name to use (ex: gcc44, clang32,...)")
	cmd.Flag.String("os", "", "explicit system name to use (ex: slc6, slc5, centos6, darwin106,...)")
	cmd.Flag.String("type", "", "explicit build variant to use (ex: opt/dbg)")
	cmd.Flag.String("cmtcfg", "", "explicit CMTCFG value to use")
	return cmd
}

func hwaf_run_cmd_asetup(cmd *commander.Command, args []string) {
	var err error
	n := "hwaf-" + cmd.Name()

	if len(args) == 0 {
		// case where we reuse a previously already asetup'ed workarea
		_, err = g_ctx.LocalCfg()
		if err == nil {
			return
		}
		err = fmt.Errorf("%v\n'hwaf asetup' called with no argument in a pristine workarea is NOT valid.", err)
		handle_err(err)
	}
	asetup := make([]string, 0, len(args))
	for _, arg := range args {
		subarg := strings.Split(arg, ",")
		for _, sarg := range subarg {
			if sarg != "" {
				asetup = append(asetup, sarg)
			}
		}
	}
	dirname, err := os.Getwd()
	handle_err(err)

	dirname, err = filepath.Abs(dirname)
	handle_err(err)

	// make sure 'hwaf init' was run at least once in this directory...
	if !is_git_repo(dirname) {
		sub := exec.Command("hwaf", "init", dirname)
		sub.Stdin = os.Stdin
		sub.Stdout = os.Stdout
		sub.Stderr = os.Stderr
		err = sub.Run()
		handle_err(err)
	}

	quiet := cmd.Flag.Lookup("q").Value.Get().(bool)
	//cfg_fname := cmd.Flag.Lookup("cfg").Value.Get().(string)
	cli_cmtcfg := cmd.Flag.Lookup("cmtcfg").Value.Get().(string)
	cli_arch := cmd.Flag.Lookup("arch").Value.Get().(string)
	cli_comp := cmd.Flag.Lookup("comp").Value.Get().(string)
	cli_os := cmd.Flag.Lookup("os").Value.Get().(string)
	cli_type := cmd.Flag.Lookup("type").Value.Get().(string)

	sitedir := g_ctx.Sitedir()
	if sitedir == "" {
		sitedir = filepath.Join("", "opt", "sw", "mana")
		g_ctx.Warn("no $HWAF_SITEDIR env. variable. will use [%s]\n", sitedir)
	}

	if !path_exists(sitedir) {
		err = fmt.Errorf("no such directory [%s]", sitedir)
		handle_err(err)
	}

	type asetup_opts struct {
		projdir string
		cmtcfg  string
	}

	pinfos, err := platform.Infos()
	handle_err(err)

	// FIXME: this should be more thought out... and structured!
	process_asetup := func(asetup []string) (asetup_opts, error) {
		var opts asetup_opts
		var err error
		unprocessed := make([]string, 0, len(asetup))
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
		case "i386":
			hwaf_arch = "i686"
		default:
			//hwaf_arch = "unknown"
			panic(fmt.Sprintf("unknown architecture [%s]", hwaf_arch))
		}
		hwaf_bld := "opt"
		for _, arg := range asetup {
			has_prefix := func(prefix string) bool {
				return strings.HasPrefix(arg, prefix)
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
			case "mana-ext":
				projname = arg
			default:
				if has_prefix("2012") || has_prefix("2013") {
					version = arg
				} else if has_prefix("gcc") || has_prefix("clang") {
					hwaf_comp = arg
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

		usr_cmtcfg := fmt.Sprintf("%s-%s-%s-%s", hwaf_arch, hwaf_os, hwaf_comp, hwaf_bld)
		opts.projdir = filepath.Join(sitedir, projname)
		if version == "" {
			// get the latest one.
			var versions []string
			versions, err = filepath.Glob(filepath.Join(opts.projdir, "*"))
			if err != nil {
				return opts, err
			}
			sort.Strings(versions)
			version = versions[len(versions)-1]
			version, _ = filepath.Abs(version)
			version = filepath.Base(version)
		}
		opts.projdir = filepath.Join(sitedir, projname, version)
		found := false
		for _, cmtcfg := range []string{
			cli_cmtcfg,
			usr_cmtcfg,
			g_ctx.Cmtcfg(),
			g_ctx.DefaultCmtcfg(),
		} {
			if cmtcfg == "" {
				continue
			}
			dir := filepath.Join(opts.projdir, cmtcfg)
			//fmt.Printf("---> [%s]...\n", dir)
			if !path_exists(dir) {
				//fmt.Printf("---> [%s]... [err]\n", dir)
				continue
			}
			opts.projdir = dir
			opts.cmtcfg = cmtcfg
			//fmt.Printf("---> [%s]... [ok]\n", dir)
			found = true
			break
		}
		if !found {
			return opts, fmt.Errorf("hwaf: could not find a suitable project")
		}
		return opts, err
	}
	opts, err := process_asetup(asetup)
	handle_err(err)

	if !quiet {
		fmt.Printf("%s: asetup workarea [%s]...\n", n, dirname)
		fmt.Printf("%s: projects=%v\n", n, opts.projdir)
		// if cfg_fname != "" {
		// 	fmt.Printf("%s: cfg-file=%s\n", n, cfg_fname)
		// }
	}

	subcmd := exec.Command(
		"hwaf", "setup",
		fmt.Sprintf("-q=%v", quiet),
		"-p", opts.projdir,
	)
	subcmd.Stdin = os.Stdin
	subcmd.Stdout = os.Stdout
	subcmd.Stderr = os.Stderr
	err = subcmd.Run()
	handle_err(err)

	lcfg_fname := filepath.Join(".hwaf", "local.conf")
	if !path_exists(lcfg_fname) {
		err = fmt.Errorf("%s: no such file [%s]", n, lcfg_fname)
		handle_err(err)
	}

	lcfg, err := gocfg.ReadDefault(lcfg_fname)
	handle_err(err)
	section := "env"
	if !lcfg.HasSection(section) {
		if !lcfg.AddSection(section) {
			err = fmt.Errorf("%s: could not create section [%s] in file [%s]",
				n, section, lcfg_fname)
			handle_err(err)
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
		if lcfg.HasOption(section, k) {
			lcfg.RemoveOption(section, k)
		}
		ok := lcfg.AddOption(section, k, v)
		if !ok {
			err = fmt.Errorf(
				"%s: could not add option [%s=%q] to file [%s]",
				n, k, v, lcfg_fname,
			)
			handle_err(err)
		}
	}
	err = lcfg.WriteFile(lcfg_fname, 0600, "")
	handle_err(err)

	// commit changes to lcfg_fname
	// FIXME: check if there is an error ?
	exec.Command("git", "add", lcfg_fname).Run()
	exec.Command("git", "commit", "-m", "asetup initialization finished").Run()

	if !quiet {
		fmt.Printf("%s: asetup workarea [%s]... [ok]\n", n, dirname)
	}
}

// EOF
