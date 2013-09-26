package main

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/gonuts/commander"
	gocfg "github.com/gonuts/config"
	"github.com/gonuts/flag"
	"github.com/hwaf/hwaf/hwaflib"
)

func hwaf_make_cmd_setup() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_setup,
		UsageLine: "setup [options] <workarea>",
		Short:     "setup an existing workarea",
		Long: `
setup sets up an existing workarea.

ex:
 $ hwaf setup
 $ hwaf setup .
 $ hwaf setup my-work-area
 $ hwaf setup -p=/opt/sw/mana/mana-core/20121207 my-work-area
 $ hwaf setup -p=/path1:/path2 my-work-area
 $ hwaf setup -cfg=${HWAF_CFG}/usr.cfg my-work-area
 $ hwaf setup -tags=ATLAS,NEED_PYCOOL my-work-area
 $ hwaf setup -variant=x86_64-slc6-gcc47-opt my-work-area
`,
		Flag: *flag.NewFlagSet("hwaf-setup", flag.ExitOnError),
	}
	cmd.Flag.String("p", "", "List of paths to projects to setup against")
	cmd.Flag.String("cfg", "", "Path to a configuration file")
	cmd.Flag.String("pkgdir", "src", "Directory under which to checkout packages")
	cmd.Flag.String("variant", "", "quadruplet (e.g. x86_64-slc6-gcc47-opt) identifying the target to build for")
	cmd.Flag.String("tags", "", "comma-separated list of tags to enable for this build")
	cmd.Flag.Bool("v", false, "enable verbose output")

	return cmd
}

func hwaf_run_cmd_setup(cmd *commander.Command, args []string) {
	var err error
	n := "hwaf-" + cmd.Name()
	dirname := "."
	switch len(args) {
	case 0:
		dirname = "."
	case 1:
		dirname = args[0]
	default:
		err = fmt.Errorf("%s: you need to give a directory name", n)
		handle_err(err)
	}

	dirname = os.ExpandEnv(dirname)
	dirname = filepath.Clean(dirname)

	verbose := cmd.Flag.Lookup("v").Value.Get().(bool)
	cfg_fname := cmd.Flag.Lookup("cfg").Value.Get().(string)
	pkgdir := cmd.Flag.Lookup("pkgdir").Value.Get().(string)
	variant := cmd.Flag.Lookup("variant").Value.Get().(string)
	tags := cmd.Flag.Lookup("tags").Value.Get().(string)

	projdirs := []string{}
	const pathsep = string(os.PathListSeparator)
	for _, v := range strings.Split(cmd.Flag.Lookup("p").Value.Get().(string), pathsep) {
		if v != "" {
			v = os.ExpandEnv(v)
			v = filepath.Clean(v)
			projdirs = append(projdirs, v)
		}
	}

	if verbose {
		fmt.Printf("%s: setup workarea [%s]...\n", n, dirname)
		fmt.Printf("%s: projects=%v\n", n, projdirs)
		if cfg_fname != "" {
			fmt.Printf("%s: cfg-file=%s\n", n, cfg_fname)
		}
	}

	if cfg_fname != "" && !path_exists(cfg_fname) {
		err = fmt.Errorf("configuration file [%s] does not exist (or is not readable)", cfg_fname)
		handle_err(err)
	}

	for _, projdir := range projdirs {
		if !path_exists(projdir) {
			err = fmt.Errorf("no such directory: [%s]", projdir)
			handle_err(err)
		}

		pinfo := filepath.Join(projdir, "project.info")
		if !path_exists(pinfo) {
			err = fmt.Errorf("no such file: [%s]", pinfo)
			handle_err(err)
		}
	}

	pwd, err := os.Getwd()
	handle_err(err)
	defer os.Chdir(pwd)

	err = os.Chdir(dirname)
	handle_err(err)

	if verbose {
		fmt.Printf("%s: create local config...\n", n)
	}

	var lcfg *gocfg.Config
	lcfg_fname := "local.conf"

	// if the user provided a configuration file use that as a default
	if cfg_fname != "" && path_exists(cfg_fname) {
		lcfg, err = gocfg.ReadDefault(cfg_fname)
		handle_err(err)
	} else {
		if path_exists(lcfg_fname) {
			lcfg, err = gocfg.ReadDefault(lcfg_fname)
			handle_err(err)
		} else {
			lcfg = gocfg.NewDefault()
		}
	}

	section := "hwaf-cfg"
	if !lcfg.HasSection(section) && !lcfg.AddSection(section) {
		err = fmt.Errorf("%s: could not create section [%s] in file [%s]",
			n, section, lcfg_fname)
		handle_err(err)
	}

	// fetch a few informations from the first project.info
	cmtcfg := g_ctx.Cmtcfg()
	//projvers := time.Now().Format("20060102")
	if len(projdirs) > 0 {
		pinfo, err := hwaflib.NewProjectInfo(filepath.Join(projdirs[0], "project.info"))
		handle_err(err)
		cmtcfg, err = pinfo.Get("CMTCFG")
		handle_err(err)
	}

	if variant != "" {
		cmtcfg = variant
	}

	if tags != "" {
		tags_slice := strings.Split(tags, ",")
		tags = strings.Join(tags_slice, " ")
	}

	for k, v := range map[string]string{
		"projects": strings.Join(projdirs, pathsep),
		"pkgdir":   pkgdir,
		"cmtcfg":   cmtcfg,
		"tags":     tags,
	} {
		if lcfg.HasOption(section, k) {
			lcfg.RemoveOption(section, k)
		}
		if !lcfg.AddOption(section, k, v) {
			err := fmt.Errorf("%s: could not add option [%s] to section [%s]",
				n, k, section,
			)
			handle_err(err)
		}
	}

	err = lcfg.WriteFile(lcfg_fname, 0600, "")
	handle_err(err)

	if verbose {
		fmt.Printf("%s: setup workarea [%s]... [ok]\n", n, dirname)
	}
}

// EOF
