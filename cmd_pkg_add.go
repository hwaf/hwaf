package main

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"strings"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
	"github.com/hwaf/hwaf/vcs"
	//gocfg "github.com/gonuts/config"
)

func hwaf_make_cmd_pkg_add() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_pkg_add,
		UsageLine: "co [options] <pkg-uri> [<local-pkg-name>]",
		Short:     "add a package to the current workarea",
		Long: `
co adds a package to the current workarea.

ex:
 $ hwaf pkg co /foo/pkg
 $ hwaf pkg co Control/AthenaKernel
 $ hwaf pkg co git://github.com/mana-fwk/mana-core-athenakernel
 $ hwaf pkg co git://github.com/mana-fwk/mana-core-athenakernel Control/AthenaKernel
 $ hwaf pkg co -b=rel/mana git://github.com/mana-fwk/mana-core-athenakernel Control/AthenaKernel
 $ hwaf pkg co -b=AthenaKernel-00-00-01 svn+ssh://svn.cern.ch/reps/atlasoff/Control/AthenaKernel Control/AthenaKernel
 $ hwaf pkg co -f=list.of.pkgs.txt
`,
		Flag: *flag.NewFlagSet("hwaf-pkg-co", flag.ExitOnError),
	}
	cmd.Flag.Bool("q", true, "only print error and warning messages, all other output will be suppressed")
	cmd.Flag.String("b", "", "branch to checkout (default=master)")
	cmd.Flag.String("f", "", "path to a file holding a list of packages to retrieve")

	return cmd
}

func hwaf_run_cmd_pkg_add(cmd *commander.Command, args []string) {
	var err error
	n := "hwaf-pkg-" + cmd.Name()
	pkguri := ""
	pkgname := ""

	switch len(args) {
	default:
		err = fmt.Errorf("%s: expects 0, 1 or 2 arguments (got %d: %v)", n, len(args), args)
		handle_err(err)
	case 2:
		pkguri = args[0]
		pkgname = args[1]
	case 1:
		pkguri = args[0]
		pkgname = ""
	case 0:
		fname := cmd.Flag.Lookup("f").Value.Get().(string)
		if fname != "" {
			f, err := os.Open(fname)
			if err != nil {
				handle_err(err)
			}
			pkgs := [][]string{}
			scnr := bufio.NewScanner(f)
			for scnr.Scan() {
				line := strings.Trim(scnr.Text(), " \n")
				if strings.HasPrefix(line, "#") {
					continue
				}
				tokens := strings.Split(line, " ")
				pkg := []string{}
				for _, tok := range tokens {
					tok = strings.Trim(tok, " \t")
					if tok != "" {
						pkg = append(pkg, tok)
					}
				}
				if len(pkg) > 0 {
					pkgs = append(pkgs, pkg)
				}
			}
			err = scnr.Err()
			if err != nil && err != io.EOF {
				handle_err(err)
			}
			quiet := cmd.Flag.Lookup("q").Value.Get().(bool)
			for _, pkg := range pkgs {
				args := []string{"pkg", "co"}
				if !quiet {
					args = append(args, "-q=0")
				}
				switch len(pkg) {
				case 1:
					args = append(args, pkg[0])
				case 2:
					args = append(args, "-b="+pkg[1], pkg[0])
				case 3:
					args = append(args, "-b="+pkg[1], pkg[0], pkg[2])
				default:
					err = fmt.Errorf("%s: invalid number of pkg-co arguments (expected [1-3], got=%d) args=%v", n, len(pkg), pkg)
					handle_err(err)
				}
				cmd := exec.Command("hwaf", args...)
				cmd.Stdout = os.Stdout
				cmd.Stderr = os.Stderr
				cmd.Stdin = os.Stdin
				err = cmd.Run()
				handle_err(err)
			}
			return
		}

		err = fmt.Errorf("%s: you need to give a package URL", n)
		handle_err(err)
	}

	quiet := cmd.Flag.Lookup("q").Value.Get().(bool)
	bname := cmd.Flag.Lookup("b").Value.Get().(string)

	if !quiet {
		fmt.Printf("%s: checkout package [%s]...\n", n, pkguri)
	}

	cfg, err := g_ctx.LocalCfg()
	handle_err(err)

	pkgdir := "src"
	if cfg.HasOption("hwaf-cfg", "pkgdir") {
		pkgdir, err = cfg.String("hwaf-cfg", "pkgdir")
		handle_err(err)
	}

	//fmt.Printf(">>> helper(pkguri=%q, pkgname=%q, pkgid=%q)...\n", pkguri, pkgname, bname)
	helper, err := vcs.NewHelper(pkguri, pkgname, bname, pkgdir)
	handle_err(err)
	defer helper.Delete()

	dir := filepath.Join(pkgdir, helper.PkgName)
	//fmt.Printf(">>> dir=%q\n", dir)

	if g_ctx.PkgDb.HasPkg(dir) {
		err = fmt.Errorf("%s: package [%s] already in db.\ndid you forget to run 'hwaf pkg rm %s' ?", n, dir, dir)
		handle_err(err)
	}

	//fmt.Printf(">>> pkgname=%q\n", helper.PkgName)
	err = helper.Checkout()
	handle_err(err)

	err = g_ctx.PkgDb.Add(helper.Type, helper.Repo, dir)
	handle_err(err)

	err = helper.Delete()
	handle_err(err)

	if !quiet {
		fmt.Printf("%s: checkout package [%s]... [ok]\n", n, pkguri)
	}
}

// EOF
