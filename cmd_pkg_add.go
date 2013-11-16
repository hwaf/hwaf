package main

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
	"sync"

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
	cmd.Flag.Bool("v", false, "enable verbose output")
	cmd.Flag.String("b", "", "branch to checkout (default=master)")
	cmd.Flag.String("f", "", "path to a file holding a list of packages to retrieve")

	return cmd
}

func hwaf_run_cmd_pkg_add(cmd *commander.Command, args []string) {
	var err error
	n := "hwaf-pkg-" + cmd.Name()

	verbose := cmd.Flag.Lookup("v").Value.Get().(bool)
	bname := cmd.Flag.Lookup("b").Value.Get().(string)

	type Request struct {
		pkguri  string
		pkgname string
		pkgtag  string
	}

	reqs := make([]Request, 0, 2)

	switch len(args) {
	default:
		err = fmt.Errorf("%s: expects 0, 1 or 2 arguments (got %d: %v)", n, len(args), args)
		handle_err(err)
	case 2:
		pkguri := args[0]
		pkgname := args[1]
		reqs = append(reqs,
			Request{
				pkguri:  pkguri,
				pkgname: pkgname,
				pkgtag:  bname,
			},
		)
	case 1:
		pkguri := args[0]
		pkgname := ""
		reqs = append(reqs,
			Request{
				pkguri:  pkguri,
				pkgname: pkgname,
				pkgtag:  bname,
			},
		)
	case 0:
		fname := cmd.Flag.Lookup("f").Value.Get().(string)
		if fname == "" {
			err = fmt.Errorf("%s: you need to give a package URL", n)
			handle_err(err)
		}
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
		for _, pkg := range pkgs {
			switch len(pkg) {
			case 1:
				reqs = append(reqs, Request{
					pkguri:  pkg[0],
					pkgname: "",
					pkgtag:  "",
				})
			case 2:
				reqs = append(reqs, Request{
					pkguri:  pkg[0],
					pkgname: "",
					pkgtag:  pkg[1],
				})
			case 3:
				reqs = append(reqs, Request{
					pkguri:  pkg[0],
					pkgname: pkg[2],
					pkgtag:  pkg[1],
				})
			default:
				err := fmt.Errorf("%s: invalid number of pkg-co arguments (expected [1-3], got=%d) args=%v", n, len(pkg), pkg)
				handle_err(err)
			}
		}
	}

	cfg, err := g_ctx.LocalCfg()
	handle_err(err)

	pkgdir := "src"
	if cfg.HasOption("hwaf-cfg", "pkgdir") {
		pkgdir, err = cfg.String("hwaf-cfg", "pkgdir")
		handle_err(err)
	}

	throttle := make(chan struct{}, 1)
	errch := make(chan error)

	var dblock sync.RWMutex
	var colock sync.RWMutex

	do_checkout := func(req Request) {
		pkguri := req.pkguri
		pkgname := req.pkgname
		bname := req.pkgtag

		throttle <- struct{}{}
		defer func() { <-throttle }()

		if verbose {
			fmt.Printf("%s: checkout package [%s]...\n", n, pkguri)
		}

		// fmt.Printf(">>> helper(pkguri=%q, pkgname=%q, pkgid=%q, pkgdir=%q)...\n", pkguri, pkgname, bname, pkgdir)
		helper, err := vcs.NewHelper(pkguri, pkgname, bname, pkgdir)
		if err != nil {
			errch <- err
			return
		}
		defer helper.Delete()

		dir := filepath.Join(helper.RepoDir, helper.PkgName)
		// fmt.Printf(">>> dir=%q\n", dir)
		// fmt.Printf(">>> helper=%#v\n", helper)

		dblock.RLock()
		if g_ctx.PkgDb.HasPkg(dir) {
			err = fmt.Errorf("%s: package [%s] already in db.\ndid you forget to run 'hwaf pkg rm %s' ?", n, dir, dir)
			errch <- err
			dblock.RUnlock()
			fmt.Printf("%s: checkout package [%s]... [err]\n", n, pkguri)
			return
		}
		dblock.RUnlock()

		//fmt.Printf(">>> pkgname=%q\n", helper.PkgName)
		if helper.Type == "git" {
			colock.Lock()
		}
		err = helper.Checkout()
		if err != nil {
			errch <- err
			if helper.Type == "git" {
				colock.Unlock()
			}
			fmt.Printf("%s: checkout package [%s]... [err]\n", n, pkguri)
			return
		}
		if helper.Type == "git" {
			colock.Unlock()
		}

		dblock.Lock()
		err = g_ctx.PkgDb.Add(helper.Type, helper.Repo, helper.RepoDir, dir)
		if err != nil {
			errch <- err
			dblock.Unlock()
			fmt.Printf("%s: checkout package [%s]... [err]\n", n, pkguri)
			return
		}
		dblock.Unlock()

		err = helper.Delete()
		if err != nil {
			errch <- err
			fmt.Printf("%s: checkout package [%s]... [err]\n", n, pkguri)
			return
		}

		if verbose {
			fmt.Printf("%s: checkout package [%s]... [ok]\n", n, pkguri)
		}
		errch <- nil
	}

	for _, req := range reqs {
		go do_checkout(req)
	}

	errs := make([]error, 0, len(reqs))
	for _ = range reqs {
		err := <-errch
		if err != nil {
			errs = append(errs, err)
		}
	}

	for _, err := range errs {
		fmt.Fprintf(os.Stderr, "**error** %v\n", err)
	}

	if len(errs) != 0 {
		os.Exit(1)
	}
}

// EOF
