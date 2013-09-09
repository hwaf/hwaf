package main_test

import (
	"fmt"
	"io/ioutil"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"text/template"
)

type pkgdef_t struct {
	Name string
	Deps []string
}

func (p pkgdef_t) BaseName() string {
	return filepath.Base(p.Name)
}

func (p pkgdef_t) TestName() string {
	return "test" + p.BaseName()
}

func (p pkgdef_t) LibName() string {
	return "Lib" + p.BaseName()
}

func (p pkgdef_t) PkgDeps() string {
	if len(p.Deps) <= 0 {
		return ""
	}
	s := []string{
		"deps: {",
		"   public: [",
	}
	for _, dep := range p.Deps {
		s = append(
			s,
			"      "+dep+",",
		)
	}
	s = append(
		s,
		"   ],",
		"},",
	)
	// reindent
	for i := range s {
		s[i] = "   " + s[i]
	}
	return strings.Join(s, "\n")
}

func (p pkgdef_t) LibUse() string {
	if len(p.Deps) <= 0 {
		return ""
	}
	s := []string{
		"use: [",
	}
	for _, dep := range p.Deps {
		s = append(
			s,
			fmt.Sprintf(`   "Lib%s",`, dep),
		)
	}
	s = append(
		s,
		"],",
	)
	// reindent
	for i := range s {
		s[i] = "   " + s[i]
	}
	return strings.Join(s, "\n")
}

func (p pkgdef_t) HdrIncludes() string {
	if len(p.Deps) <= 0 {
		return ""
	}
	s := make([]string, 0, len(p.Deps))
	for _, dep := range p.Deps {
		s = append(
			s,
			fmt.Sprintf(`#include "%s/Lib%s.hxx"`, dep, dep),
		)
	}
	return strings.Join(s, "\n")
}

func (p pkgdef_t) HdrMembers() string {
	if len(p.Deps) <= 0 {
		return ""
	}
	s := make([]string, 0, len(p.Deps))
	for _, dep := range p.Deps {
		s = append(
			s,
			fmt.Sprintf(`   CLib%s m_%s;`, dep, dep),
		)
	}
	return strings.Join(s, "\n")
}

func (p pkgdef_t) LibMembers() string {
	if len(p.Deps) <= 0 {
		return ""
	}
	s := make([]string, 0, len(p.Deps))
	for _, dep := range p.Deps {
		s = append(
			s,
			fmt.Sprintf(`   m_%s.f();`, dep),
		)
	}
	return strings.Join(s, "\n")
}

func (p pkgdef_t) TestUse() string {
	if len(p.Deps) <= 0 {
		return "use: [" + p.LibName() + "],"
	}
	s := []string{
		"use: [",
	}
	for _, dep := range p.Deps {
		s = append(
			s,
			fmt.Sprintf(`   "Lib%s",`, dep),
		)
	}
	s = append(
		s,
		fmt.Sprintf(`   "%s",`, p.LibName()),
		"],",
	)
	// reindent
	for i := range s {
		s[i] = "   " + s[i]
	}
	return strings.Join(s, "\n")
}

func TestMultiProject(t *testing.T) {
	workdir, err := ioutil.TempDir("", "hwaf-test-")
	if err != nil {
		t.Fatalf(err.Error())
	}
	defer os.RemoveAll(workdir)
	//fmt.Printf(">>> test: %s\n", workdir)

	err = os.Chdir(workdir)
	if err != nil {
		t.Fatalf(err.Error())
	}

	hwaf, err := newlogger("hwaf.log")
	if err != nil {
		t.Fatalf(err.Error())
	}
	defer hwaf.Close()

	const hscript_tmpl = `
## -*- yaml -*-

package: {
   name: "{{.Name}}",
   authors: ["me"],
{{.PkgDeps}}
}

configure: {
   tools: ["compiler_c", "compiler_cxx", "find_python"],
   env: {
      PYTHONPATH: "${INSTALL_AREA}/python:${PYTHONPATH}",
   },
}

build: {
   {{.TestName}}: {
      features: "cxx cxxprogram hwaf_install_headers hwaf_utest",
      includes: "includes",
      export_includes: "includes",
      cwd: "includes",
      source: "src/{{.TestName}}.cxx",
      {{.TestUse}}
   },

   {{.LibName}}: {
      features: "cxx cxxshlib hwaf_install_headers hwaf_export_lib",
      includes: "includes",
      export_includes: "includes",
      cwd: "includes",
      source: "src/{{.LibName}}.cxx",
      {{.LibUse}}
   },
}
`

	const src_lib_tmpl = `
#include <iostream>
#include "{{.BaseName}}/{{.LibName}}.hxx"

C{{.LibName}}::C{{.LibName}}()
{
   std::cout << "c-tor C{{.LibName}}" << std::endl;
}

C{{.LibName}}::~C{{.LibName}}()
{
   std::cout << "d-tor C{{.LibName}}" << std::endl;
}

void
C{{.LibName}}::f()
{
   std::cout << "C{{.LibName}}.f" << std::endl;
{{.LibMembers}}
}
`

	const hdr_lib_tmpl = `
#ifndef __{{.LibName}}_hxx__
#define __{{.LibName}}_hxx__ 1

// --------------------------------------
{{.HdrIncludes}}

#ifdef _MSC_VER
#define DllExport __declspec( dllexport )
#else
#define DllExport
#endif

class DllExport C{{.LibName}}
{
public:
    C{{.LibName}}();
    ~C{{.LibName}}();
    void f();
private:
{{.HdrMembers}}
};

#endif // !__{{.LibName}}_hxx__
`
	const src_tst_tmpl = `
#include <iostream>
#include "{{.BaseName}}/{{.LibName}}.hxx"

int main(int argc, char **argv)
{
  std::cout << "Testing binary for package {{.Name}}\n"
            << "argc: " << argc << "\n"
            << "argv: " << argv << "\n";

  C{{.LibName}} o;
  o.f();
  return 0;
}
`

	gen_tmpl := func(fname string, text string, data interface{}) error {
		f, err := os.Create(fname)
		if err != nil {
			return err
		}
		defer f.Close()
		t := template.New("tmpl")
		template.Must(t.Parse(text))
		err = t.Execute(f, data)
		if err != nil {
			return err
		}
		return f.Sync()
	}

	gen_proj := func(projname string, projdeps []string, pkgdefs []pkgdef_t) error {
		var err error
		projdir := filepath.Join(workdir, projname)
		err = os.MkdirAll(projdir, 0777)
		if err != nil {
			return err
		}

		pkgdir := filepath.Join(projdir, "src")
		err = os.MkdirAll(pkgdir, 0777)
		if err != nil {
			return err
		}

		gen_pkg := func(pkg pkgdef_t) error {
			var err error
			// create pkg structure
			for _, dir := range []string{
				filepath.Join(pkg.Name, "includes", pkg.Name),
				filepath.Join(pkg.Name, "src"),
			} {
				err = os.MkdirAll(dir, 0777)
				if err != nil {
					return err
				}
			}

			// create hscript
			fname := filepath.Join(pkg.Name, "hscript.yml")
			err = gen_tmpl(fname, hscript_tmpl, pkg)
			if err != nil {
				return err
			}

			// header
			fname = filepath.Join(pkg.Name, "includes", pkg.Name, fmt.Sprintf("%s.hxx", pkg.LibName()))
			err = gen_tmpl(fname, hdr_lib_tmpl, pkg)
			if err != nil {
				return err
			}

			// lib
			fname = filepath.Join(pkg.Name, "src", fmt.Sprintf("%s.cxx", pkg.LibName()))
			err = gen_tmpl(fname, src_lib_tmpl, pkg)
			if err != nil {
				return err
			}

			// test
			fname = filepath.Join(pkg.Name, "src", fmt.Sprintf("%s.cxx", pkg.TestName()))
			err = gen_tmpl(fname, src_tst_tmpl, pkg)
			if err != nil {
				return err
			}

			return err
		}

		//fmt.Printf("pkgdir=%q\n", pkgdir)
		err = os.Chdir(pkgdir)
		if err != nil {
			return err
		}

		for _, pkg := range pkgdefs {
			err = gen_pkg(pkg)
			if err != nil {
				return err
			}
		}

		//fmt.Printf("projdir=%q\n", projdir)
		err = os.Chdir(projdir)
		if err != nil {
			return err
		}

		gen_projdeps := func(projdeps []string) string {
			if len(projdeps) <= 0 {
				return ""
			}
			projpath := make([]string, 0, len(projdeps))
			for _, dep := range projdeps {
				projpath = append(
					projpath,
					filepath.Join(workdir, dep, "install-area"),
				)
			}
			return strings.Join(projpath, ":")
		}
		// build project
		for _, cmd := range [][]string{
			{"hwaf", "init", "-v=1", "."},
			{"hwaf", "setup", "-v=1", "-p=" + gen_projdeps(projdeps)},
			{"hwaf", "configure"},
			{"hwaf"},
			{"hwaf", "check"},
		} {
			err := hwaf.Run(cmd[0], cmd[1:]...)
			if err != nil {
				hwaf.Display()
				t.Fatalf("cmd %v failed: %v", cmd, err)
			}
		}
		return err
	}

	for _, table := range []struct {
		projname string
		projdeps []string
		pkgdefs  []pkgdef_t
	}{
		{
			"project_001",
			[]string{},
			[]pkgdef_t{
				{
					"project_001_pkg_001",
					[]string{},
				},
				{
					"project_001_pkg_002",
					[]string{},
				},
				{
					"project_001_pkg_003",
					[]string{},
				},
			},
		},

		{
			"project_002",
			[]string{"project_001"},
			[]pkgdef_t{
				{
					"project_002_pkg_001",
					[]string{"project_001_pkg_001"},
				},
				{
					"project_002_pkg_002",
					[]string{"project_001_pkg_001", "project_001_pkg_002"},
				},
				{
					"project_002_pkg_003",
					[]string{"project_001_pkg_001", "project_001_pkg_003"},
				},
			},
		},

		{
			"project_003",
			[]string{"project_001"},
			[]pkgdef_t{
				{
					"project_003_pkg_001",
					[]string{"project_001_pkg_001"},
				},
				{
					"project_003_pkg_002",
					[]string{"project_001_pkg_001", "project_001_pkg_002"},
				},
				{
					"project_003_pkg_003",
					[]string{"project_001_pkg_001", "project_001_pkg_003"},
				},
			},
		},

		{
			"project_004",
			[]string{"project_002", "project_003"},
			[]pkgdef_t{
				{
					"project_004_pkg_001",
					[]string{
						"project_001_pkg_001",
						"project_002_pkg_001",
					},
				},
				{
					"project_004_pkg_002",
					[]string{
						"project_001_pkg_001",
						"project_001_pkg_002",
						"project_002_pkg_001",
						"project_003_pkg_002",
					},
				},
				{
					"project_004_pkg_003",
					[]string{
						"project_001_pkg_001",
						"project_001_pkg_003",
						"project_002_pkg_001",
						"project_002_pkg_003",
						"project_003_pkg_001",
						"project_003_pkg_003",
					},
				},
			},
		},
	} {
		err = gen_proj(table.projname, table.projdeps, table.pkgdefs)
		if err != nil {
			t.Fatalf("project [%v]: %v\n", table.projname, err)
		}
	}

	//hwaf.Display()
}

// EOF
