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
## automatically generated from a hscript
## do NOT edit.

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
    {{with .Tools}}{{. | gen_wscript_tools}}{{end}}
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
    {{with .Tools}}{{. | gen_wscript_tools}}{{end}}
    {{with .HwafCall}}{{. | gen_wscript_hwaf_call}}
    {{end}}
    {{.Env | gen_wscript_env}}
    {{range .Stmts}}##{{. | gen_wscript_stmts}}
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
    {{with .Tools}}{{. | gen_wscript_tools}}{{end}}
    {{with .HwafCall}}{{. | gen_wscript_hwaf_call}}
    {{end}}
    {{range .Stmts}}##{{. | gen_wscript_stmts}}
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
		"gen_wscript_pkg_deps":  gen_wscript_pkg_deps,
		"gen_wscript_tools":     gen_wscript_tools,
		"gen_wscript_hwaf_call": gen_wscript_hwaf_call,
		"gen_wscript_env":       gen_wscript_env,
		"gen_wscript_stmts":     gen_wscript_stmts,
		"gen_wscript_targets":   gen_wscript_targets,
	})
	template.Must(t.Parse(text))
	return t.Execute(w, data)
}

func w_gen_taglist(tags string) []string {
	str := make([]string, 0, strings.Count(tags, "&"))
	for _, v := range strings.Split(tags, "&") {
		v = strings.Trim(v, " ")
		if len(v) > 0 {
			str = append(str, v)
		}
	}
	return str
}

func w_gen_valdict_switch_str(indent string, values [][2]string) string {
	o := make([]string, 0, len(values))
	o = append(o, "(")
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
	o = append(o, indent+")")
	return strings.Join(o, "\n")
}

func w_py_hlib_value(indent string, fctname string, x Value) []string {
	str := make([]string, 0)

	values := make([][2]string, 0, len(x.Set))
	for _, v := range x.Set {
		k := v.Tag
		values = append(values, [2]string{k, w_py_strlist(v.Value)})
	}
	str = append(
		str,
		fmt.Sprintf(
			"ctx.%s(%q, %s)",
			fctname,
			x.Name,
			w_gen_valdict_switch_str(indent, values),
		),
	)

	return str
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

func gen_wscript_tools(tools []string) string {
	const indent = "    "
	str := []string{""}

	for _, tool := range tools {
		str = append(
			str,
			fmt.Sprintf("ctx.load(%q)", tool),
			fmt.Sprintf("try: ctx.%s()", tool),
			"except AttributeError: pass",
			"",
		)
	}

	// reindent:
	for i, s := range str[1:] {
		str[i+1] = indent + s
	}

	return strings.Join(str, "\n")
}

func gen_wscript_hwaf_call(calls []string) string {
	const indent = "    "
	str := []string{""}

	for _, script := range calls {
		str = append(
			str,
			fmt.Sprintf(
				"ctx._hwaf_load_fct(PACKAGE['name'], %q)",
				script,
			),
			"",
		)
	}

	// reindent:
	for i, s := range str[1:] {
		str[i+1] = indent + s
	}

	return strings.Join(str, "\n")
}

func gen_wscript_env(env Env_t) string {
	const indent = "    "
	var str []string

	//str = append(str, "## environment -- begin")
	for k, _ := range env {
		str = append(str, fmt.Sprintf("ctx.hwaf_declare_runtime_env(%q)", k))
		// 	switch len(values) {
		// 	case 0:
		// 	case 1:
		// 		if len(values.Set) > 1 {
		// 			// str = append(
		// 			// 	str,
		// 			// 	fmt.Sprintf("%s: {"),
		// 			// )
		// 		} else {
		// 			kvs := values.Set[0]
		// 			for k, v := range kvs {

		// 			}
		// 		}
		// 	default:
		// 	}
	}
	//str = append(str, "## environment -- end")

	// // reindent:
	// for i, s := range str[1:] {
	// 	str[i+1] = indent + s
	// }

	return strings.Join(str, "\n")
}

func gen_wscript_stmts(stmt Stmt) string {
	const indent = "    "
	var str []string
	switch x := stmt.(type) {
	case *MacroStmt:
		str = []string{fmt.Sprintf("## macro %v", stmt)}
		str = append(
			str,
			w_py_hlib_value(indent, "hwaf_declare_macro", x.Value)...,
		)

	case *MacroAppendStmt:
		str = []string{fmt.Sprintf("## macro_append %v", stmt)}
		str = append(
			str,
			w_py_hlib_value(indent, "hwaf_macro_append", x.Value)...,
		)

	case *MacroPrependStmt:
		str = []string{fmt.Sprintf("## macro_prepend %v", stmt)}
		str = append(
			str,
			w_py_hlib_value(indent, "hwaf_macro_prepend", x.Value)...,
		)

	case *MacroRemoveStmt:
		str = []string{fmt.Sprintf("## macro_remove %v", stmt)}
		str = append(
			str,
			w_py_hlib_value(indent, "hwaf_macro_remove", x.Value)...,
		)

	case *TagStmt:
		str = []string{fmt.Sprintf("## tag %v", stmt)}
		values := w_py_strlist(x.Content)
		str = append(str,
			"ctx.hwaf_declare_tag(",
			fmt.Sprintf("%s%q,", indent, x.Name),
			fmt.Sprintf("%scontent=[%s]", indent, values),
			")",
		)

	case *ApplyTagStmt:
		str = []string{fmt.Sprintf("## apply_tag %v", stmt)}
		str = append(
			str,
			fmt.Sprintf("ctx.hwaf_apply_tag(%q)", x.Value.Set[0].Value[0]),
		)

	case *PathStmt:
		str = []string{fmt.Sprintf("## path %v", stmt)}
		str = append(
			str,
			w_py_hlib_value(indent, "hwaf_declare_path", x.Value)...,
		)

	case *PathAppendStmt:
		str = []string{fmt.Sprintf("## path_append %v", stmt)}
		str = append(
			str,
			w_py_hlib_value(indent, "hwaf_path_append", x.Value)...,
		)

	case *PathPrependStmt:
		str = []string{fmt.Sprintf("## path_prepend %v", stmt)}
		str = append(
			str,
			w_py_hlib_value(indent, "hwaf_path_prepend", x.Value)...,
		)

	case *PathRemoveStmt:
		str = []string{fmt.Sprintf("## path_remove %v", stmt)}
		str = append(
			str,
			w_py_hlib_value(indent, "hwaf_path_remove", x.Value)...,
		)

	//case *ApplyPatternStmt:

	default:
		str = []string{fmt.Sprintf("### **** statement %T (%v)", stmt, stmt)}
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
		target_name := tgt.Target
		if target_name == "" {
			target_name = tgt.Name
		}
		str = append(str,
			"ctx(",
			fmt.Sprintf("%sfeatures = %q,", indent, features),
			fmt.Sprintf("%sname     = %q,", indent, tgt.Name),
			fmt.Sprintf("%starget   = %q,", indent, target_name),
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
