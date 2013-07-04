package main

import (
	"bufio"
	"fmt"
	"io"
	"net/url"
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
	case 1:
		pkguri = args[0]
		pkgname = ""
	case 2:
		pkguri = args[0]
		pkgname = args[1]
	default:
		fname := cmd.Flag.Lookup("f").Value.Get().(string)
		if fname != "" {
			f, err := os.Open(fname)
			if err != nil {
				handle_err(err)
			}
			pkgs := [][]string{}
			scnr := bufio.NewScanner(f)
			for scnr.Scan() {
				line := scnr.Text()
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

	pkguri = os.ExpandEnv(pkguri)

	// FIXME: shouldn't this be refactorized ?
	if strings.HasPrefix(pkguri, "git@github.com:") {
		pkguri = strings.Replace(
			pkguri,
			"git@github.com:",
			"git+ssh://git@github.com/",
			1)
	}

	//pkguri = filepath.Clean(pkguri)

	uri, err := url.Parse(pkguri)
	handle_err(err)
	// fmt.Printf(">>> [%v]\n", uri)
	// fmt.Printf("    Scheme: %q\n", uri.Scheme)
	// fmt.Printf("    Opaque: %q\n", uri.Opaque)
	// fmt.Printf("    Host:   %q\n", uri.Host)
	// fmt.Printf("    Path:   %q\n", uri.Path)
	// fmt.Printf("    Fragm:  %q\n", uri.Fragment)

	switch pkgname {
	case "":
		pkgname = uri.Path
	default:
		pkgname = os.ExpandEnv(pkgname)
		pkgname = filepath.Clean(pkgname)
	}

	// FIXME: hack. we need a better "plugin architecture" for this...
	if uri.Scheme == "" && !path_exists(uri.Path) {
		if svnroot := os.Getenv("SVNROOT"); svnroot != "" {
			pkguri = svnroot + "/" + pkguri
			pkguri = os.ExpandEnv(pkguri)
			uri, err = url.Parse(pkguri)
			handle_err(err)
			// fmt.Printf(">>> [%v]\n", uri)
			// fmt.Printf("    Scheme: %q\n", uri.Scheme)
			// fmt.Printf("    Opaque: %q\n", uri.Opaque)
			// fmt.Printf("    Host:   %q\n", uri.Host)
			// fmt.Printf("    Path:   %q\n", uri.Path)
			// fmt.Printf("    Fragm:  %q\n", uri.Fragment)
		}
	}

	quiet := cmd.Flag.Lookup("q").Value.Get().(bool)
	bname := cmd.Flag.Lookup("b").Value.Get().(string)

	if !quiet {
		fmt.Printf("%s: checkout package [%s]...\n", n, pkguri)
	}

	cfg, err := g_ctx.LocalCfg()
	handle_err(err)

	pkgdir := "src"
	if cfg.HasOption("hwaf-cfg", "cmtpkgs") {
		pkgdir, err = cfg.String("hwaf-cfg", "cmtpkgs")
		handle_err(err)
	}

	dir := filepath.Join(pkgdir, pkgname)
	if filepath.IsAbs(pkgname) {
		dir = pkgname
	}

	switch uri.Scheme {
	case "svn", "svn+ssh":
		if !path_exists(filepath.Dir(dir)) {
			err = os.MkdirAll(filepath.Dir(dir), 0755)
			handle_err(err)
		}
		repo := pkguri
		if bname != "" {
			// can't use filepath.Join as it may mess-up the uri.Scheme
			repo = strings.Join([]string{pkguri, "tags", bname}, "/")
		} else {
			// can't use filepath.Join as it may mess-up the uri.Scheme
			repo = strings.Join([]string{pkguri, "trunk"}, "/")
		}

		if g_ctx.PkgDb.HasPkg(dir) {
			err = fmt.Errorf("%s: package [%s] already in db.\ndid you forget to run 'hwaf pkg rm %s' ?", n, dir, dir)
			handle_err(err)
		}

		err = vcs.Svn.Create(dir, repo)
		handle_err(err)

		err = g_ctx.PkgDb.Add("svn", repo, dir)
		handle_err(err)
		return
	}

	if g_ctx.PkgDb.HasPkg(dir) {
		err = fmt.Errorf("%s: package [%s] already in db.\ndid you forget to run 'hwaf pkg rm %s' ?", n, dir, dir)
		handle_err(err)
	}

	err = vcs.Git.Create(dir, pkguri)
	handle_err(err)

	if bname != "" {
		git := exec.Command(
			"git", "checkout", bname,
		)
		git.Dir = dir
		if !quiet {
			git.Stdout = os.Stdout
			git.Stderr = os.Stderr
		}
		err = git.Run()
		handle_err(err)
	}

	err = g_ctx.PkgDb.Add("git", pkguri, dir)
	handle_err(err)

	if !quiet {
		fmt.Printf("%s: checkout package [%s]... [ok]\n", n, pkguri)
	}
}

// EOF
