package platform

import (
	"bufio"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"sort"
	"strings"

	gocfg "github.com/gonuts/config"
)

func uname(opts ...string) (string, error) {

	cmd := exec.Command("uname", opts...)
	bout, err := cmd.Output()
	if err != nil {
		return "", err
	}
	out := strings.Trim(string(bout), " \r\n")
	return out, err
}

func infos() (Platform, error) {
	var err error
	var plat Platform

	table := map[string]string{
		"System":    "-s",
		"Node":      "-n",
		"Release":   "-r",
		"Version":   "-v",
		"Machine":   "-m",
		"Processor": "-p",
	}

	for n, arg := range table {
		var v string
		v, err = uname(arg)
		if err != nil {
			return plat, err
		}
		table[n] = v
	}

	plat.System = table["System"]
	plat.Node = table["Node"]
	plat.Release = table["Release"]
	plat.Version = table["Version"]
	plat.Machine = table["Machine"]
	plat.Processor = table["Processor"]

	err = plat.init_dist()

	return plat, err
}

func parse_dist_files(fnames []string) (distname, distvers string, err error) {
	distname = ""
	distvers = ""

	re_release_filename := regexp.MustCompile(`(\w+)(-release|_version)`)
	re_lsb_release_version := regexp.MustCompile(`(.+) release ([\d.]+)[^(]*(?:\((.+)\))?`)
	re_release_version := regexp.MustCompile(`([^0-9]+)(?: release )?([\d.]+)[^(]*(?:\((.+)\))?`)

	if !sort.StringsAreSorted(fnames) {
		sort.Strings(fnames)
	}

	for _, fname := range fnames {
		m := re_release_filename.FindStringSubmatch(fname)
		if m == nil {
			continue
		}
		distname = m[1]
		//fmt.Printf(">>> [%s]\n    [%v] => %q\n", fname, m, distname)
		distfile := fname

		f, err2 := os.Open(distfile)
		defer f.Close()
		if err2 != nil {
			continue
		}

		var line string
		line, err2 = bufio.NewReader(f).ReadString('\n')
		if err2 != nil {
			continue
		}
		//distid := ""

		m = re_lsb_release_version.FindStringSubmatch(line)
		if m == nil {
			// pre-LSB.
			m = re_release_version.FindStringSubmatch(line)
			if m == nil {
				// not supported.
				//fmt.Printf("** [%s] wrong format (%v)\n", distfile, strings.Trim(line, " \r\n"))
				continue
			}
		}
		// LSB format: "distro release x.x (codename)"
		distfullname := m[1]
		distvers = m[2]
		//distid = m[3]
		//fmt.Printf(">>> %v (%q %q)\n", m, distfullname, distvers)
		match := func(pattern string) bool {
			matched, err := regexp.MatchString(pattern, distfullname)
			if err != nil {
				return false
			}
			return matched
		}

		if match(`Red.*?Hat.*?Enterprise.*?Linux.*?`) {
			// rel := strings.Split(distvers, ".")
			// major := rel[0]
			// //minor := rel[1]
			// distver = major
			distname = "rhel"

		} else if match(`Red.*?Hat.*?Linux.*?`) {
			// rel := strings.Split(distvers, ".")
			// major := rel[0]
			// //minor := rel[1]
			// distver = major
			distname = "rh"

		} else if match(`CERN.*?E.*?Linux.*?`) {
			distname = "cel"

		} else if match(`Scientific.*?Linux.*?CERN.*?`) {

			// rel := strings.Split(distvers, ".")
			// major := rel[0]
			// //minor := rel[1]
			// distver = major
			distname = "slc"
		} else if match(`Scientific.*?Linux.*?`) {

			// rel := strings.Split(distvers, ".")
			// major := rel[0]
			// //minor := rel[1]
			// distver = major
			distname = "sl"

		} else if match(`Fedora.*?`) {
			distname = "fedora"

		} else {
			// not a supported distribution ?
			continue
		}
		//fmt.Printf("dist=%q distvers=%v\n", distname, distvers)
		return distname, distvers, nil
	}

	for _, args := range [][]string{
		{"/etc/os-release", "ID", "VERSION_ID"},
		{"/etc/lsb-release", "DISTRIB_ID", "DISTRIB_RELEASE"},
	} {
		fname := args[0]
		id_str := args[1]
		vers_str := args[2]
		//fmt.Printf("--> [%s]\n", fname)
		idx := sort.SearchStrings(fnames, fname)
		if !(idx < len(fnames) && fnames[idx] == fname) {
			continue
		}

		cfg, err := gocfg.ReadDefault(fname)
		if err != nil {
			//fmt.Printf("++ %v\n", err)
			continue
		}

		d_name, err := cfg.RawString("DEFAULT", id_str)
		if err == nil {
			distname = strings.Trim(d_name, `"'`)
		} else {
			//fmt.Printf("++ %v\n", err)
			continue
		}
		d_vers, err := cfg.RawString("DEFAULT", vers_str)
		if err == nil {
			distvers = strings.Trim(d_vers, `"'`)
		} else {
			// distvers is optional...

			//fmt.Printf("++ %v\n", err)
			//continue
		}
		return distname, distvers, nil
	}

	return "", "", fmt.Errorf("platform: unsupported linux distribution")
}

func (p *Platform) init_dist() error {
	var err error

	distname := strings.ToLower(p.System)
	distvers := ""

	switch p.System {
	case "Linux":
		var files []string
		files, err = filepath.Glob(filepath.Join("/etc", "*"))
		if err != nil {
			return err
		}
		sort.Strings(files)
		distname, distvers, err = parse_dist_files(files)
		if err != nil {
			return err
		}
		if distname == "" {
			return fmt.Errorf("platform: unsupported linux distribution")
		}

	case "Darwin":
		distvers = p.Release
		vers, err := exec.Command("sw_vers", "-productVersion").Output()
		if err == nil {
			distvers = strings.Trim(string(vers), " \r\n")
		}
		distname = "darwin"

	default:
		panic(fmt.Sprintf("platform: unknown platform [%s]", p.System))
	}

	p.DistName = distname
	p.DistVers = distvers
	return err
}

// EOF
