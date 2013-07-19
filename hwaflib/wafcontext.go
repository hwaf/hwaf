package hwaflib

import (
	"fmt"
	"io/ioutil"
	"os"
	"path/filepath"
	"strings"

	"github.com/gonuts/yaml"
	"github.com/hwaf/hwaf/hlib"
)

// WafBootstrap makes sure 'waf' is ready to run
func (ctx *Context) init_waf_ctx() error {
	var err error

	// at this point, ctx.workarea should be ok.
	root, err := ctx.Workarea()
	if err != nil {
		return err
	}

	fnames := make([]string, 0, 2)
	err = filepath.Walk(
		root,
		func(path string, info os.FileInfo, err error) error {
			//fmt.Printf(">>> [%s]...\n", path)
			fname := filepath.Base(path)
			if fname == "hscript.yml" {
				fnames = append(fnames, path)
			}
			return err
		})
	if err != nil {
		return err
	}

	//fmt.Printf("fnames: %v\n", fnames)
	wscripts := make([]string, 0, len(fnames))
	for _, fname := range fnames {
		path := filepath.Dir(fname)
		wscript := filepath.Join(path, "wscript")
		if path_exists(wscript) {
			err = os.Rename(wscript, wscript+".bak")
			if err != nil {
				return err
			}
		}
		err = waf_gen_wscript(wscript)
		wscripts = append(wscripts, wscript)
		if err != nil {
			break
		}
	}
	ctx.atexit = append(ctx.atexit, func() {
		for _, fname := range wscripts {
			//fmt.Printf(">>> removing [%s]...\n", fname)
			keep := os.Getenv("HWAF_KEEP_WSCRIPT")
			if keep == "" || keep == "0" {
				os.Remove(fname)
			}
		}
	})

	return err
}

func waf_gen_wscript(fname string) error {
	var err error
	hscript := filepath.Join(filepath.Dir(fname), "hscript.yml")
	f, err := os.Open(hscript)
	if err != nil {
		return err
	}
	// FIXME: don't gobble up the whole file. read piecewise
	buf, err := ioutil.ReadAll(f)
	if err != nil {
		return err
	}

	f, err = os.Create(fname)
	if err != nil {
		return err
	}
	defer f.Close()

	err = waf_gen_wscript_hdr(f)
	if err != nil {
		return err
	}

	data := make(map[string]interface{})
	err = goyaml.Unmarshal(buf, data)
	if err != nil {
		return fmt.Errorf("error decoding file [%s]: %v", hscript, err)
	}

	wscript, err := waf_get_wscript(data)
	if err != nil {
		return err
	}

	enc := hlib.NewWscriptEncoder(f)
	if enc == nil {
		return fmt.Errorf("error creating WscriptEncoder")
	}

	err = enc.Encode(wscript)
	if err != nil {
		return err
	}

	return err
}

func waf_get_yaml_map(data interface{}) map[string]interface{} {
	out := make(map[string]interface{})
	vdata := data.(map[interface{}]interface{})
	for k, v := range vdata {
		kk := k.(string)
		out[kk] = v
	}
	return out
}

func waf_get_wscript(data map[string]interface{}) (*hlib.Wscript_t, error) {
	var err error
	var wscript hlib.Wscript_t

	wpkg := &wscript.Package

	// ---------- package section ---------------------------------------------
	if _, ok := data["package"]; !ok {
		return nil, fmt.Errorf("missing mandatory 'package' section")
	}

	pkg := waf_get_yaml_map(data["package"])
	wpkg.Name = pkg["name"].(string)

	if _, ok := pkg["authors"]; ok {
		switch v := pkg["authors"].(type) {
		case []interface{}:
			for _, vv := range v {
				wpkg.Authors = append(wpkg.Authors, hlib.Author(vv.(string)))
			}
		case string:
			wpkg.Authors = append(wpkg.Authors, hlib.Author(v))
		default:
			return nil, fmt.Errorf("unknown type (%T) for 'authors' field", v)
		}
	}

	if _, ok := pkg["managers"]; ok {
		switch v := pkg["managers"].(type) {
		case []interface{}:
			for _, vv := range v {
				wpkg.Managers = append(wpkg.Managers, hlib.Manager(vv.(string)))
			}
		case string:
			wpkg.Managers = append(wpkg.Managers, hlib.Manager(v))
		default:
			return nil, fmt.Errorf("unknown type (%T) for 'managers' field", v)
		}
	}

	if _, ok := pkg["version"]; ok {
		wpkg.Version = hlib.Version(pkg["version"].(string))
	}

	if _, ok := pkg["deps"]; ok {
		if _, ok := pkg["deps"].(map[interface{}]interface{}); !ok {
			return nil, fmt.Errorf("'deps' field has to be a map")
		}
		deps := waf_get_yaml_map(pkg["deps"])

		all_deps := make(map[string]int)
		if _, ok := deps["public"]; ok {
			pub_deps := deps["public"].([]interface{})
			for _, idep := range pub_deps {
				dep := idep.(string)
				all_deps[dep] = len(wpkg.Deps)
				wpkg.Deps = append(
					wpkg.Deps,
					hlib.Dep_t{
						Name: dep,
						Type: hlib.PublicDep,
					},
				)
			}
		}

		if _, ok := deps["private"]; ok {
			pri_deps := deps["private"].([]interface{})
			for _, idep := range pri_deps {
				dep := idep.(string)
				all_deps[dep] = len(wpkg.Deps)
				wpkg.Deps = append(
					wpkg.Deps,
					hlib.Dep_t{
						Name: dep,
						Type: hlib.PrivateDep,
					},
				)
			}
		}

		if _, ok := deps["runtime"]; ok {
			r_deps := deps["runtime"].([]interface{})
			for _, idep := range r_deps {
				dep := idep.(string)
				if idx, ok := all_deps[dep]; ok {
					wpkg.Deps[idx].Type |= hlib.RuntimeDep
				} else {
					wpkg.Deps = append(
						wpkg.Deps,
						hlib.Dep_t{
							Name: dep,
							Type: hlib.RuntimeDep,
						},
					)
				}
			}
		}

	}

	// ---------- options section ---------------------------------------------
	if _, ok := data["options"]; ok {
		wopt := &wscript.Options
		opt := waf_get_yaml_map(data["options"])
		if _, ok := opt["tools"]; ok {
			tools := opt["tools"].([]interface{})
			for _, itool := range tools {
				wopt.Tools = append(wopt.Tools, itool.(string))
			}
		}

		if _, ok := opt["hwaf-call"]; ok {
			calls := opt["hwaf-call"].([]interface{})
			for _, icall := range calls {
				wopt.HwafCall = append(wopt.HwafCall, icall.(string))
			}
		}
	}

	// ---------- configure section -------------------------------------------
	if _, ok := data["configure"]; ok {
		wcfg := &wscript.Configure
		cfg := waf_get_yaml_map(data["configure"])
		if _, ok := cfg["tools"]; ok {
			tools := cfg["tools"].([]interface{})
			for _, itool := range tools {
				wcfg.Tools = append(wcfg.Tools, itool.(string))
			}
		}
		// FIXME:
		//  handle 'env' section
		if _, ok := cfg["env"]; ok {
			env := waf_get_yaml_map(cfg["env"])
			for k, iv := range env {
				switch v := iv.(type) {
				case string:
					if strings.HasSuffix(v, fmt.Sprintf(":${%s}", k)) {
						// gamble: path_prepend
						str := v[:len(v)-len(fmt.Sprintf(":${%s}", k))]
						stmt := hlib.PathPrependStmt{
							Value: hlib.Value{
								Name: k,
								Set: []hlib.KeyValue{
									{Tag: "default", Value: []string{str}},
								},
							},
						}
						wcfg.Stmts = append(
							wcfg.Stmts,
							&stmt,
						)
					} else if strings.HasPrefix(v, fmt.Sprintf("${%s}:", k)) {
						// gamble: path_append
						str := v[len(fmt.Sprintf("${%s}:", k)):]
						stmt := hlib.PathAppendStmt{
							Value: hlib.Value{
								Name: k,
								Set: []hlib.KeyValue{
									{Tag: "default", Value: []string{str}},
								},
							},
						}
						wcfg.Stmts = append(
							wcfg.Stmts,
							&stmt,
						)
					} else {
						// gamble declare_path
						stmt := hlib.PathStmt{
							Value: hlib.Value{
								Name: k,
								Set: []hlib.KeyValue{
									{Tag: "default", Value: []string{v}},
								},
							},
						}
						wcfg.Stmts = append(
							wcfg.Stmts,
							&stmt,
						)
					}
				default:
					return nil, fmt.Errorf("unknown type (%T) for 'configure.env' field", v)
				}
			}
		}

		// FIXME:
		//  handle 'declare-tags' section
		if _, ok := cfg["declare-tags"]; ok {
			add_tag := func(name string, data ...string) {
				content := make([]string, len(data))
				copy(content, data)
				stmt := hlib.TagStmt{
					Name:    name,
					Content: content,
				}
				wcfg.Stmts = append(
					wcfg.Stmts,
					&stmt,
				)
			}
			switch tags := cfg["declare-tags"].(type) {
			case []interface{}:
				for _, iv := range tags {
					tags := waf_get_yaml_map(iv)
					for name, content := range tags {
						switch content := content.(type) {
						case string:
							add_tag(name, content)
						case []interface{}:
							tag_content := make([]string, 0, len(content))
							for _, tag := range content {
								tag_content = append(tag_content, tag.(string))
							}
							add_tag(name, tag_content...)
						case []string:
							add_tag(name, content...)
						default:
							return nil, fmt.Errorf("unknown type (%T) for 'configure.declare-tags' field", tags)
						}
					}
				}
			default:
				return nil, fmt.Errorf("unknown type (%T) for 'configure.declare-tags' field", tags)

			}
		}

		//  handle 'apply-tag' section
		if _, ok := cfg["apply-tags"]; ok {
			add_tag := func(data ...string) {
				tags := make([]string, len(data))
				copy(tags, data)
				stmt := hlib.ApplyTagStmt{
					Value: hlib.Value{
						Name: "",
						Set: []hlib.KeyValue{
							{Tag: "default", Value: tags},
						},
					},
				}
				wcfg.Stmts = append(
					wcfg.Stmts,
					&stmt,
				)
			}
			switch tags := cfg["apply-tags"].(type) {
			case string:
				add_tag(tags)
			case []string:
				add_tag(tags...)
			case []interface{}:
				for _, iv := range tags {
					switch iv := iv.(type) {
					case string:
						add_tag(iv)
					default:
						return nil, fmt.Errorf("unknown type (%T) for 'configure.apply-tags' field", tags)

					}
				}
			default:
				return nil, fmt.Errorf("unknown type (%T) for 'configure.apply-tags' field", tags)

			}
		}

		// FIXME:
		//  handle 'export-tools' section ?

		if _, ok := cfg["hwaf-call"]; ok {
			calls := cfg["hwaf-call"].([]interface{})
			for _, icall := range calls {
				wcfg.HwafCall = append(wcfg.HwafCall, icall.(string))
			}
		}
	}

	// ---------- build section -----------------------------------------------
	if _, ok := data["build"]; ok {
		wbld := &wscript.Build
		bld := waf_get_yaml_map(data["build"])
		if _, ok := bld["tools"]; ok {
			tools := bld["tools"].([]interface{})
			for _, itool := range tools {
				wbld.Tools = append(wbld.Tools, itool.(string))
			}
		}
		if _, ok := bld["hwaf-call"]; ok {
			calls := bld["hwaf-call"].([]interface{})
			for _, icall := range calls {
				wbld.HwafCall = append(wbld.HwafCall, icall.(string))
			}
		}
		// FIXME:
		//  handle 'env' section
		//  handle 'tag' section

		tgt_names := make([]string, 0, len(bld))
		for k, _ := range bld {
			if k != "hwaf-call" && k != "tools" && k != "env" {
				tgt_names = append(tgt_names, k)
			}
		}
		for _, n := range tgt_names {
			tgt := waf_get_yaml_map(bld[n])
			wtgt := hlib.Target_t{
				Name:   n,
				KwArgs: make(map[string][]hlib.Value),
			}
			if v, ok := tgt["features"]; ok {
				switch v := v.(type) {
				case string:
					tmps := strings.Split(v, " ")
					for _, tmp := range tmps {
						tmp = strings.Trim(tmp, " ")
						if tmp != "" {
							wtgt.Features = append(wtgt.Features, tmp)
						}
					}

				case []interface{}:
					for _, iv := range v {
						v := iv.(string)
						tmps := strings.Split(v, " ")
						for _, tmp := range tmps {
							tmp = strings.Trim(tmp, " ")
							if tmp != "" {
								wtgt.Features = append(wtgt.Features, tmp)
							}
						}
					}

				case []string:
					for _, iv := range v {
						tmps := strings.Split(iv, " ")
						for _, tmp := range tmps {
							tmp = strings.Trim(tmp, " ")
							if tmp != "" {
								wtgt.Features = append(wtgt.Features, tmp)
							}
						}
					}

				default:
					return nil, fmt.Errorf("unknown type (%T) for target [%s] in 'build' section", v, n)
				}
				delete(tgt, "features")
			}

			if _, ok := tgt["name"]; ok {
				nn := tgt["name"].(string)
				if nn != wtgt.Name {
					return nil, fmt.Errorf("inconsistency in target [%s] declaration: name=%q but key=%q", n, nn, wtgt.Name)
				}
				delete(tgt, "name")
			}

			if _, ok := tgt["target"]; ok {
				wtgt.Target = tgt["target"].(string)
				delete(tgt, "target")
			}

			cnvmap := map[string]*[]hlib.Value{
				"source":          &wtgt.Source,
				"use":             &wtgt.Use,
				"defines":         &wtgt.Defines,
				"cflags":          &wtgt.CFlags,
				"cxxflags":        &wtgt.CxxFlags,
				"linkflags":       &wtgt.LinkFlags,
				"shlibflags":      &wtgt.ShlibFlags,
				"stlibflags":      &wtgt.StlibFlags,
				"rpath":           &wtgt.RPath,
				"includes":        &wtgt.Includes,
				"export_includes": &wtgt.ExportIncludes,
				"install_path":    &wtgt.InstallPath,
			}
			for k, v := range tgt {
				vv := waf_gen_hvalue_from(k, v)
				if dst, ok := cnvmap[k]; ok {
					*dst = append(*dst, vv)
				} else {
					wtgt.KwArgs[k] = append(wtgt.KwArgs[k], vv)
				}
			}
			wbld.Targets = append(wbld.Targets, wtgt)
		}

	}
	return &wscript, err
}

func waf_gen_hvalue_from(name string, data interface{}) hlib.Value {
	value := hlib.Value{Name: name}

	_add_to_value := func(v *hlib.Value, kv hlib.KeyValue) {
		for i, kkv := range v.Set {
			if kkv.Tag == kv.Tag {
				v.Set[i].Value = append(v.Set[i].Value, kv.Value...)
				return
			}
		}
		v.Set = append(v.Set, kv)
	}

	_add_value := func(value *hlib.Value, strs ...string) {
		v := make([]string, len(strs))
		copy(v, strs)
		_add_to_value(value, hlib.KeyValue{
			Tag:   "default",
			Value: v,
		})
	}

	switch data := data.(type) {
	case string:
		_add_value(&value, data)

	case []string:
		_add_value(&value, data...)

	case []interface{}:
		for _, v := range data {
			switch data := v.(type) {
			case string:
				_add_value(&value, data)

			case []string:
				_add_value(&value, data...)
			default:
				panic(fmt.Errorf("unknown type (%T)", data))
			}
		}
	default:
		panic(fmt.Errorf("unknown type (%T)", data))
	}
	return value
}

func waf_gen_wscript_hdr(f *os.File) error {
	var err error
	_, err = fmt.Fprintf(f, `
## waf imports
import waflib.Logs as msg

`)
	if err != nil {
		return err
	}

	return err
}

func waf_gen_wscript_pkg(data map[string]interface{}, f *os.File) error {
	var err error
	_, err = fmt.Fprintf(f, `
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
`)
	return err
}

// EOF
