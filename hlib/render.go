package hlib

import (
	"fmt"
	"io"
	"reflect"
	"strconv"
	"strings"
	"text/template"
)

type WscriptEncoder struct {
	w io.Writer
}

func NewWscriptEncoder(w io.Writer) *WscriptEncoder {
	return &WscriptEncoder{w: w}
}

func (enc *WscriptEncoder) Encode(wscript *Wscript_t) error {
	var err error

	_, err = fmt.Fprintf(
		enc.w,
		`## -*- python -*-

## waf imports
import waflib.Logs as msg
`,
	)
	if err != nil {
		return err
	}

	// generate package header
	const pkg_hdr_tmpl = `
PACKAGE = {
    "name":    "{{.Name}}",
    "authors": {{.Authors | as_pylist}},
{{if .Managers}}    "managers": {{.Managers | as_pylist}},{{end}}
{{if .Version}}    "version":  "{{.Version}}",{{end}}
}

### ---------------------------------------------------------------------------
def pkg_deps(ctx):
    {{. | gen_wscript_pkg_deps}}
    return # pkg_deps
`
	err = w_tmpl(enc.w, pkg_hdr_tmpl, wscript.Package)
	if err != nil {
		return err
	}

	// generate options - section
	err = w_tmpl(
		enc.w,
		`

### ---------------------------------------------------------------------------
def options(ctx):
    {{range .Tools}}ctx.load("{{.}}")
    {{end}}
    return # options
`,
		wscript.Options,
	)
	if err != nil {
		return err
	}

	// generate configure - section
	err = w_tmpl(
		enc.w,
		`

### ---------------------------------------------------------------------------
def configure(ctx):
    {{range .Tools}}ctx.load("{{.}}")
    {{end}}
    return # configure
`,
		wscript.Configure,
	)
	if err != nil {
		return err
	}

	// generate build - section
	err = w_tmpl(
		enc.w,
		`

### ---------------------------------------------------------------------------
def build(ctx):
    {{range .Tools}}ctx.load("{{.}}")
    {{end}}
    {{with .Targets}}{{. | gen_wscript_targets}}{{end}}
    return # build
`,
		wscript.Build,
	)
	if err != nil {
		return err
	}

	_, err = fmt.Fprintf(
		enc.w,
		"\n## EOF ##\n",
	)
	if err != nil {
		return err
	}

	return err
}

func w_tmpl(w io.Writer, text string, data interface{}) error {
	t := template.New("wscript")
	t.Funcs(template.FuncMap{
		"trim": strings.TrimSpace,
		"as_pylist": func(alist interface{}) string {
			rv := reflect.ValueOf(alist)
			str := make([]string, 0, rv.Len())
			for i := 0; i < rv.Len(); i++ {
				s := rv.Index(i)
				str = append(str, fmt.Sprintf("%q", s))
			}
			return "[" + strings.Join(str, ", ") + "]"
		},
		"gen_wscript_pkg_deps": gen_wscript_pkg_deps,
		"gen_wscript_targets":  gen_wscript_targets,
	})
	template.Must(t.Parse(text))
	return t.Execute(w, data)
}

func w_py_strlist(str []string) string {
	o := make([]string, 0, len(str))
	for _, v := range str {
		vv, err := strconv.Unquote(v)
		if err != nil {
			vv = v
		}
		if strings.HasPrefix(vv, `"`) && strings.HasSuffix(vv, `"`) {
			if len(vv) > 1 {
				vv = vv[1 : len(vv)-1]
			}
		}
		o = append(o, fmt.Sprintf("%q", vv))
	}
	return strings.Join(o, ", ")
}

func gen_wscript_pkg_deps(pkg Package_t) string {
	const indent = "    "
	var str []string
	public_deps := make([]Dep_t, 0, len(pkg.Deps))
	private_deps := make([]Dep_t, 0, len(pkg.Deps))
	runtime_deps := make([]Dep_t, 0, len(pkg.Deps))
	for _, dep := range pkg.Deps {
		if dep.Type.HasMask(RuntimeDep) {
			runtime_deps = append(runtime_deps, dep)
		}
		if dep.Type.HasMask(PublicDep) {
			public_deps = append(public_deps, dep)
		}
		if dep.Type.HasMask(PrivateDep) {
			private_deps = append(private_deps, dep)
		}
	}

	str = append(str, "")
	if len(public_deps) > 0 {
		str = append(str, "## public dependencies")
		for _, dep := range public_deps {
			str = append(
				str,
				fmt.Sprintf(
					"ctx.use_pkg(%q, version=%q, public=True)",
					dep.Name,
					dep.Version,
				),
			)
		}
		str = append(str, "")
	} else {
		str = append(str, "## no public dependencies")
	}

	if len(private_deps) > 0 {
		str = append(str, "## private dependencies")
		for _, dep := range private_deps {
			str = append(
				str,
				fmt.Sprintf(
					"ctx.use_pkg(%q, version=%q, private=True)",
					dep.Name,
					dep.Version,
				),
			)
		}
		str = append(str, "")
	} else {
		str = append(str, "## no private dependencies")
	}

	if len(runtime_deps) > 0 {
		str = append(str, "## runtime dependencies")
		for _, dep := range runtime_deps {
			str = append(
				str,
				fmt.Sprintf(
					"ctx.use_pkg(%q, version=%q, runtime=True)",
					dep.Name,
					dep.Version,
				),
			)
		}
	} else {
		str = append(str, "## no runtime dependencies")
	}

	// reindent:
	for i, s := range str[1:] {
		str[i+1] = indent + s
	}

	return strings.Join(str, "\n")
}

func gen_wscript_targets(tgts Targets_t) string {
	const indent = "    "
	var str []string

	cnv_values := func(values []Value) []string {
		out := make([]string, 0, len(values))
		for _, v := range values {
			// FIXME what about the non-default values ??
			out = append(out, v.Set[0].Value...)
		}
		return out
	}

	for i, tgt := range tgts {
		if i != 0 {
			str = append(str, "")
		}
		srcs := cnv_values(tgt.Source)
		features := strings.Join(tgt.Features, " ")
		str = append(str,
			"ctx(",
			fmt.Sprintf("%sfeatures = %q,", indent, features),
			fmt.Sprintf("%sname     = %q,", indent, tgt.Name),
			fmt.Sprintf("%ssource   = [%s],", indent, w_py_strlist(srcs)),
		)

		for _, vv := range []struct {
			hdr    string
			values []Value
		}{
			{"use", tgt.Use},
			{"defines", tgt.Defines},
			{"cflags", tgt.CFlags},
			{"cxxflags", tgt.CxxFlags},
			{"linkflags", tgt.LinkFlags},
			{"shlibflags", tgt.ShlibFlags},
			{"stlibflags", tgt.StlibFlags},
			{"rpath", tgt.RPath},
			{"includes", tgt.Includes},
			{"export_includes", tgt.ExportIncludes},
			{"install_path", tgt.InstallPath},
		} {
			if len(vv.values) > 0 {
				vals := cnv_values(vv.values)
				str = append(str,
					fmt.Sprintf(
						"%s%s = [%s],",
						indent,
						vv.hdr,
						w_py_strlist(vals),
					),
				)
			}
		}

		for kk, vv := range tgt.KwArgs {
			if len(vv) > 0 {
				vals := cnv_values(vv)
				str = append(str,
					fmt.Sprintf(
						"%s%s = [%s],",
						indent,
						kk,
						w_py_strlist(vals),
					),
				)
			}
		}
		str = append(str,
			")",
		)

	}

	// reindent:
	for i, s := range str[1:] {
		str[i+1] = indent + s
	}

	return strings.Join(str, "\n")
}

// EOF
