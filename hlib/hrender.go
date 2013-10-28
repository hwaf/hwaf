package hlib

import (
	"fmt"
	"io"
	"reflect"
	"strconv"
	"strings"
	"text/template"
)

type HscriptYmlEncoder struct {
	w io.Writer
}

func NewHscriptYmlEncoder(w io.Writer) *HscriptYmlEncoder {
	return &HscriptYmlEncoder{w: w}
}

func (enc *HscriptYmlEncoder) Encode(wscript *Wscript_t) error {
	var err error

	// generate package header ------------------------------------------------
	const pkg_hdr_tmpl = `
## package header
package: {
    name:    {{.Name}},
    authors: {{.Authors | as_hlist}},
{{if .Managers}}    managers: {{.Managers | as_hlist}},{{end}}
{{if .Version}}    version:  "{{.Version}}",{{end}}
    deps: {
{{. | gen_hscript_pkg_deps}}
    }
}
`
	err = h_tmpl(enc.w, pkg_hdr_tmpl, wscript.Package)
	if err != nil {
		return err
	}

	// generate options - section ---------------------------------------------
	err = h_tmpl(
		enc.w,
		`
options: {
    tools: [{{range .Tools}}{{.}}{{end}}],
}
`,
		wscript.Options,
	)
	if err != nil {
		return err
	}

	// generate configure - section -------------------------------------------
	err = h_tmpl(
		enc.w,
		`
configure: {
    tools: [{{range .Tools}}{{.}}{{end}}],
    env: {
{{.Stmts | gen_hscript_env}}
    },
    alias: {
{{.Stmts | gen_hscript_aliases}}
    },
}
`,
		wscript.Configure,
	)
	if err != nil {
		return err
	}

	// generate build - section -----------------------------------------------
	err = h_tmpl(
		enc.w,
		`
build: {
{{with .Targets}}{{. | gen_hscript_targets}}{{end}}
}
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

func h_tmpl(w io.Writer, text string, data interface{}) error {
	t := template.New("hscript")
	t.Funcs(template.FuncMap{
		"trim": strings.TrimSpace,
		"as_hlist": func(alist interface{}) string {
			rv := reflect.ValueOf(alist)
			str := make([]string, 0, rv.Len())
			for i := 0; i < rv.Len(); i++ {
				s := rv.Index(i)
				str = append(str, fmt.Sprintf("%s", s))
			}
			return "[" + strings.Join(str, ", ") + "]"
		},
		"gen_hscript_pkg_deps": gen_hscript_pkg_deps,
		"gen_hscript_env":      gen_hscript_env,
		"gen_hscript_aliases":  gen_hscript_aliases,
		"gen_hscript_targets":  gen_hscript_targets,
	})
	template.Must(t.Parse(text))
	return t.Execute(w, data)
}

func gen_hscript_pkg_deps(pkg Package_t) string {
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

	if len(public_deps) > 0 {
		str = append(str, "public: [")
		for _, dep := range public_deps {
			str = append(str, fmt.Sprintf("%s%s,", indent, dep.Name))
		}
		str = append(str, "],")
	} else {
		str = append(str, "public: [],")
	}

	if len(private_deps) > 0 {
		str = append(str, "private: [")
		for _, dep := range private_deps {
			str = append(str, fmt.Sprintf("%s%s,", indent, dep.Name))
		}
		str = append(str, "],")
	} else {
		str = append(str, "private: [],")
	}

	if len(runtime_deps) > 0 {
		str = append(str, "runtime: [")
		for _, dep := range runtime_deps {
			str = append(str, fmt.Sprintf("%s%s,", indent, dep.Name))
		}
		str = append(str, "],")
	} else {
		str = append(str, "runtime: [],")
	}

	// reindent:
	for i, s := range str {
		str[i] = indent + indent + s
	}

	return strings.Join(str, "\n")
}

func gen_hscript_env(stmts []Stmt) string {
	const indent = "    "
	var str []string

	for _, stmt := range stmts {
		switch stmt := stmt.(type) {
		case *MacroStmt:
			str = append(str,
				h_py_hlib_value(indent, stmt.Value)...,
			)
		}
	}
	// reindent:
	for i, s := range str {
		str[i] = indent + indent + s
	}

	return strings.Join(str, "\n")
}

func gen_hscript_aliases(stmts []Stmt) string {
	const indent = "    "
	var str []string

	for _, stmt := range stmts {
		switch stmt := stmt.(type) {
		case *AliasStmt:
			str = append(str,
				h_py_hlib_value(indent, stmt.Value)...,
			)
		}
	}
	// reindent:
	for i, s := range str {
		str[i] = indent + indent + s
	}

	return strings.Join(str, "\n")
}

func gen_hscript_targets(tgts Targets_t) string {
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

	for _, tgt := range tgts {
		str = append(str, "")
		str = append(str, fmt.Sprintf("%s: {", tgt.Name))
		srcs := cnv_values(tgt.Source)
		str = append(str,
			fmt.Sprintf("%sfeatures: %q,", indent, strings.Join(tgt.Features, " ")),
			fmt.Sprintf("%ssource:   [%s],", indent, w_py_strlist(srcs)),
		)

		if tgt.Group != "" {
			str = append(
				str,
				fmt.Sprintf("%sgroup:    %q,", indent, tgt.Group),
			)
		}

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
		} {
			if len(vv.values) > 0 {
				vals := cnv_values(vv.values)
				str = append(str,
					fmt.Sprintf(
						"%s%s: [%s],",
						indent,
						vv.hdr,
						w_py_strlist(vals),
					),
				)
			}
		}

		if len(tgt.Env) > 0 {
			str = append(str,
				fmt.Sprintf("%senv: {", indent),
			)
			for hdr, value := range tgt.Env {
				vals := cnv_values([]Value{value})
				str = append(str,
					fmt.Sprintf(
						"%s%s: [%s],",
						indent+indent,
						hdr,
						w_py_strlist(vals),
					),
				)
			}
			str = append(str,
				indent+"},",
			)
		}

		for hdr, values := range tgt.KwArgs {
			if len(values) > 0 {
				vals := cnv_values(values)
				str = append(str,
					fmt.Sprintf(
						"%s%s: [%s],",
						indent,
						hdr,
						w_py_strlist(vals),
					),
				)
			}

		}
		str = append(str,
			"},",
		)

	}

	str = append(str, "")
	str = append(str, "hwaf-call: [],")
	// reindent:
	for i, s := range str {
		str[i] = indent + s
	}

	return strings.Join(str, "\n")
}

func h_py_hlib_value(indent string, x Value) []string {
	str := make([]string, 0)

	values := make([][2]string, 0, len(x.Set))
	for _, v := range x.Set {
		k := v.Tag
		values = append(values, [2]string{k, w_py_strlist(v.Value)})
	}
	if len(x.Set) > 1 {
		str = append(
			str,
			fmt.Sprintf(
				"%s: %s,",
				x.Name,
				h_gen_valdict_switch_str(indent, values),
			),
		)
	} else {
		vv := fmt.Sprintf("%s", values[0][1])
		vv, _ = strconv.Unquote(vv)
		v_fmt := "%s: %q,"
		// if values[0][1] == "" {
		// 	v_fmt = "%s: %q,"
		// }
		str = append(
			str,
			fmt.Sprintf(
				v_fmt,
				x.Name,
				vv,
			),
		)
	}
	return str
}

func h_gen_valdict_switch_str(indent string, values [][2]string) string {
	o := make([]string, 0, len(values))
	o = append(o, "[")
	for _, v := range values {
		tags := w_gen_taglist(v[0])
		key_fmt := "(%s)"
		if strings.Count(v[0], "&") <= 0 {
			key_fmt = "%s"
		}
		val_fmt := "%s"
		if strings.Count(v[1], ",") > 0 {
			val_fmt = "[%s]"
		}
		if len(v[1]) == 0 {
			val_fmt = "%q"
		}

		o = append(o,
			fmt.Sprintf(
				"%s  {%s: %s},",
				indent,
				fmt.Sprintf(key_fmt, w_py_strlist(tags)),
				fmt.Sprintf(val_fmt, v[1]),
			),
		)
	}
	o = append(o, indent+"]")
	return strings.Join(o, "\n")
}

// EOF
