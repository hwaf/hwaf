package main

import (
	"fmt"
	"os"
	"os/user"
	"path/filepath"
	"strings"
	"text/template"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
)

func hwaf_make_cmd_pkg_create() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_pkg_create,
		UsageLine: "create [options] <pkg-full-path>",
		Short:     "create a new package in the current workarea",
		Long: `
create creates a new package in the current workarea.

ex:
 $ hwaf pkg create MyPath/MyPackage
`,
		Flag: *flag.NewFlagSet("hwaf-pkg-create", flag.ExitOnError),
	}
	cmd.Flag.Bool("q", true, "only print error and warning messages, all other output will be suppressed")
	cmd.Flag.String("authors", "", "comma-separated list of authors for the new package")
	return cmd
}

func hwaf_run_cmd_pkg_create(cmd *commander.Command, args []string) {
	var err error
	n := "hwaf-pkg-" + cmd.Name()
	pkgpath := ""
	switch len(args) {
	case 1:
		pkgpath = args[0]
	default:
		err = fmt.Errorf("%s: you need to give a package (full) path", n)
		handle_err(err)
	}

	quiet := cmd.Flag.Lookup("q").Value.Get().(bool)
	authors := func() []string {
		authors := cmd.Flag.Lookup("authors").Value.Get().(string)
		out := make([]string, 0, 1)
		for _, s := range strings.Split(authors, ",") {
			s = strings.Trim(s, " ")
			if s == "" {
				continue
			}
			out = append(out, s)
		}
		return out
	}()

	if len(authors) == 0 {
		usr, err := user.Current()
		handle_err(err)
		//fmt.Printf(">>>>> %v\n", usr)
		usrname := usr.Name
		if usrname == "" {
			usrname = usr.Username
		}
		authors = []string{usrname}
	}

	if !quiet {
		fmt.Printf("%s: create package [%s]...\n", n, pkgpath)
	}

	cfg, err := g_ctx.LocalCfg()
	handle_err(err)

	pkgdir := "src"
	if cfg.HasOption("hwaf-cfg", "pkgdir") {
		pkgdir, err = cfg.String("hwaf-cfg", "pkgdir")
		handle_err(err)
	}

	dir := filepath.Join(pkgdir, pkgpath)
	if path_exists(dir) {
		err = fmt.Errorf("%s: directory [%s] already exists on filesystem", n, dir)
		handle_err(err)
	}

	err = os.MkdirAll(dir, 0755)
	handle_err(err)

	if g_ctx.PkgDb.HasPkg(dir) {
		err = fmt.Errorf("%s: a package with name [%s] already exists", n, dir)
		handle_err(err)
	}

	pkgname := filepath.Base(pkgpath)

	// create generic structure...
	for _, d := range []string{
		//"cmt",
		pkgname,
		"src",
	} {
		err = os.MkdirAll(filepath.Join(dir, d), 0755)
		handle_err(err)
	}

	wscript, err := os.Create(filepath.Join(dir, "wscript"))
	handle_err(err)
	defer func() {
		err = wscript.Sync()
		handle_err(err)
		err = wscript.Close()
		handle_err(err)
	}()

	const txt = `# -*- python -*-
# automatically generated wscript

import waflib.Logs as msg

PACKAGE = {
    'name': '{{.FullName}}',
    'author': [{{.Authors | printlst }}], 
}

def pkg_deps(ctx):
    # put your package dependencies here.
    # e.g.:
    # ctx.use_pkg('AtlasPolicy')
    return

def configure(ctx):
    msg.debug('[configure] package name: '+PACKAGE['name'])
    return

def build(ctx):
    # build artifacts
    # e.g.:
    # ctx.build_complib(
    #    name = '{{.Name}}',
    #    source = 'src/*.cxx src/components/*.cxx',
    #    use = ['lib1', 'lib2', 'ROOT', 'boost', ...],
    # )
    # ctx.install_headers()
    # ctx.build_pymodule(source=['python/*.py'])
    # ctx.install_joboptions(source=['share/*.py'])
    return
`
	/* fill the template */
	pkg := struct {
		FullName string
		Name     string
		Authors  []string
	}{
		FullName: pkgpath,
		Name:     pkgname,
		Authors:  authors,
	}
	tmpl := template.New("wscript").Funcs(template.FuncMap{
		"printlst": func(lst []string) string {
			out := []string{}
			for idx, s := range lst {
				s = strings.Trim(s, " ")
				if s == "" {
					continue
				}
				comma := ","
				if idx+1 == len(lst) {
					comma = ""
				}
				out = append(out, fmt.Sprintf("%q%s", s, comma))
			}
			return strings.Join(out, " ")
		},
	})
	tmpl, err = tmpl.Parse(txt)
	handle_err(err)
	err = tmpl.Execute(wscript, &pkg)
	handle_err(err)

	err = g_ctx.PkgDb.Add("local", "", dir)
	handle_err(err)

	if !quiet {
		fmt.Printf("%s: create package [%s]... [ok]\n", n, pkgpath)
	}
}

// EOF
