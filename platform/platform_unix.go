package platform

import (
	"bufio"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strings"
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

func (p *Platform) init_dist() error {
	var err error

	distname := strings.ToLower(p.System)
	distvers := ""

	re_release_filename := regexp.MustCompile(`(\w+)[-_](release|version)`)
	re_lsb_release_version := regexp.MustCompile(`(.+) release ([\d.]+)[^(]*(?:\((.+)\))?`)
	//re_release_version := regexp.MustCompile(`([^0-9]+)(?: release )?([\d.]+)[^(]*(?:\((.+)\))?`)

	switch p.System {
	case "Linux":
		distfullname := ""
		distfile := ""
		var files []string
		files, err = filepath.Glob(filepath.Join("/etc", "*"))
		if err != nil {
			return err
		}
		for _, fname := range files {
			m := re_release_filename.FindStringSubmatch(fname)
			if m == nil {
				continue
			}
			distname = m[1]
			//fmt.Printf(">>> [%s]\n    [%v] => %q\n", fname, m, distname)
			distfile = fname
			break
		}
		if distname == "" {
			return fmt.Errorf("platform: unsupported linux distribution")
		}
		var f *os.File
		f, err = os.Open(distfile)
		if err != nil {
			return err
		}
		defer f.Close()

		var line string
		line, err = bufio.NewReader(f).ReadString('\n')
		if err != nil {
			return err
		}
		//distid := ""
		m := re_lsb_release_version.FindStringSubmatch(line)
		if m == nil {
			// pre-LSB. not supported.
			return fmt.Errorf("platform: unsupported linux distribution")
		}
		// LSB format: "distro release x.x (codename)"
		distfullname = m[1]
		distvers = m[2]
		//distid = m[3]
		//fmt.Printf(">>> %v (%q %q %q)\n", m, distfullname, distvers, distid)
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

		} else if match(``) {

		} else {

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
