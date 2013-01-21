package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
)

func hwaf_make_cmd_asetup() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_asetup,
		UsageLine: "asetup [options] <workarea>",
		Short:     "setup a workarea with Athena-like defaults",
		Long: `
asetup sets up a workarea with Athena-like defaults.

ex:
 $ mkdir my-work-area && cd my-work-area
 $ hwaf asetup
 $ hwaf asetup mana,20121207
 $ hwaf asetup mana 20121207 32b
 $ hwaf asetup mana 20121207 64b
`,
		Flag: *flag.NewFlagSet("hwaf-setup", flag.ExitOnError),
	}
	//cmd.Flag.String("p", "", "List of paths to projects to setup against")
	//cmd.Flag.String("cfg", "", "Path to a configuration file")
	cmd.Flag.Bool("q", true, "only print error and warning messages, all other output will be suppressed")

	return cmd
}

func hwaf_run_cmd_asetup(cmd *commander.Command, args []string) {
	var err error
	n := "hwaf-" + cmd.Name()

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
	cfg_fname := cmd.Flag.Lookup("cfg").Value.Get().(string)

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

	// FIXME: this should be more thought out... and structured!
	process_asetup := func(asetup []string) (asetup_opts, error) {
		var opts asetup_opts
		var err error
		unprocessed := make([]string, 0, len(asetup))
		projname := "mana-core"
		version := "20121212"
		hwaf_os := strings.ToLower(runtime.GOOS)
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

		opts.cmtcfg = fmt.Sprintf("%s-%s-%s-%s", hwaf_arch, hwaf_os, hwaf_comp, hwaf_bld)
		opts.projdir = filepath.Join(sitedir, projname, version, opts.cmtcfg)

		return opts, err
	}
	opts, err := process_asetup(asetup)
	handle_err(err)

	if !quiet {
		fmt.Printf("%s: asetup workarea [%s]...\n", n, dirname)
		fmt.Printf("%s: projects=%v\n", n, opts.projdir)
		if cfg_fname != "" {
			fmt.Printf("%s: cfg-file=%s\n", n, cfg_fname)
		}
	}

	subcmd := exec.Command(
		"hwaf", "setup",
		"-p", opts.projdir,
		"-q", fmt.Sprintf("%v", quiet),
	)
	if !quiet {
		subcmd.Stdin = os.Stdin
		subcmd.Stdout = os.Stdout
		subcmd.Stderr = os.Stderr
	}
	err = subcmd.Run()
	handle_err(err)

	if !quiet {
		fmt.Printf("%s: asetup workarea [%s]... [ok]\n", n, dirname)
	}
}

// EOF
