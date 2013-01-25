// Package vcs eases interactions with various Versioned Control Systems.
//
// This is mainly reaped off golang.org/src/cmd/go/vcs.go
package vcs

import (
	"bytes"
	"fmt"
	"os"
	"os/exec"
	//"path/filepath"
	"regexp"
	"strings"
)

// A Cmd describes how to use a version control system
// like Mercurial, Git, or Subversion.
type Cmd struct {
	name    string
	cmd     string // name of binary to invoke command
	verbose bool   // printout what we do

	createCmd   string // command to download a fresh copy of a repository
	downloadCmd string // command to download updates into an existing repository

	tagCmd         []tagCmd // commands to list tags
	tagLookupCmd   []tagCmd // commands to lookup tags before running tagSyncCmd
	tagSyncCmd     string   // command to sync to specific tag
	tagSyncDefault string   // command to sync to default tag

	scheme  []string
	pingCmd string
}

// A tagCmd describes a command to list available tags
// that can be passed to tagSyncCmd.
type tagCmd struct {
	cmd     string // command to list tags
	pattern string // regexp to extract tags from list
}

// List lists the known version control systems
var List = []*Cmd{
	Hg,
	Git,
	Svn,
	Bzr,
}

// ByCmd returns the version control system for the given
// command name (hg, git, svn, bzr).
func ByCmd(cmd string) *Cmd {
	for _, vcs := range List {
		if vcs.cmd == cmd {
			return vcs
		}
	}
	return nil
}

// Hg describes how to use Mercurial.
var Hg = &Cmd{
	name: "Mercurial",
	cmd:  "hg",

	createCmd:   "clone -U {repo} {dir}",
	downloadCmd: "pull",

	// We allow both tag and branch names as 'tags'
	// for selecting a version.  This lets people have
	// a go.release.r60 branch and a go1 branch
	// and make changes in both, without constantly
	// editing .hgtags.
	tagCmd: []tagCmd{
		{"tags", `^(\S+)`},
		{"branches", `^(\S+)`},
	},
	tagSyncCmd:     "update -r {tag}",
	tagSyncDefault: "update default",

	scheme:  []string{"https", "http", "ssh"},
	pingCmd: "identify {scheme}://{repo}",
}

// Git describes how to use Git.
var Git = &Cmd{
	name: "Git",
	cmd:  "git",

	createCmd:   "clone {repo} {dir}",
	downloadCmd: "fetch",

	tagCmd: []tagCmd{
		// tags/xxx matches a git tag named xxx
		// origin/xxx matches a git branch named xxx on the default remote repository
		{"show-ref", `(?:tags|origin)/(\S+)$`},
	},
	tagLookupCmd: []tagCmd{
		{"show-ref tags/{tag} origin/{tag}", `((?:tags|origin)/\S+)$`},
	},
	tagSyncCmd:     "checkout {tag}",
	tagSyncDefault: "checkout origin/master",

	scheme:  []string{"git", "https", "http", "git+ssh"},
	pingCmd: "ls-remote {scheme}://{repo}",
}

// Bzr describes how to use Bazaar.
var Bzr = &Cmd{
	name: "Bazaar",
	cmd:  "bzr",

	createCmd: "branch {repo} {dir}",

	// Without --overwrite bzr will not pull tags that changed.
	// Replace by --overwrite-tags after http://pad.lv/681792 goes in.
	downloadCmd: "pull --overwrite",

	tagCmd:         []tagCmd{{"tags", `^(\S+)`}},
	tagSyncCmd:     "update -r {tag}",
	tagSyncDefault: "update -r revno:-1",

	scheme:  []string{"https", "http", "bzr", "bzr+ssh"},
	pingCmd: "info {scheme}://{repo}",
}

// Svn describes how to use Subversion.
var Svn = &Cmd{
	name: "Subversion",
	cmd:  "svn",
	//verbose: true,

	createCmd:   "checkout {repo} {dir}",
	downloadCmd: "update",

	// There is no tag command in subversion.
	// The branch information is all in the path names.

	scheme:  []string{"https", "http", "svn", "svn+ssh"},
	pingCmd: "info {scheme}://{repo}",
}

func (v *Cmd) String() string {
	return v.name
}

// run runs the command line cmd in the given directory.
// keyval is a list of key, value pairs.  run expands
// instances of {key} in cmd into value, but only after
// splitting cmd into individual arguments.
// If an error occurs, run prints the command line and the
// command's combined stdout+stderr to standard error.
// Otherwise run discards the command's output.
func (v *Cmd) run(dir string, cmd string, keyval ...string) error {
	_, err := v.run1(dir, cmd, keyval, true)
	return err
}

// runVerboseOnly is like run but only generates error output to standard error in verbose mode.
func (v *Cmd) runVerboseOnly(dir string, cmd string, keyval ...string) error {
	_, err := v.run1(dir, cmd, keyval, false)
	return err
}

// runOutput is like run but returns the output of the command.
func (v *Cmd) runOutput(dir string, cmd string, keyval ...string) ([]byte, error) {
	return v.run1(dir, cmd, keyval, true)
}

// run1 is the generalized implementation of run and runOutput.
func (v *Cmd) run1(dir string, cmdline string, keyval []string, verbose bool) ([]byte, error) {
	m := make(map[string]string)
	for i := 0; i < len(keyval); i += 2 {
		m[keyval[i]] = keyval[i+1]
	}
	args := strings.Fields(cmdline)
	for i, arg := range args {
		args[i] = expand(m, arg)
	}

	cmd := exec.Command(v.cmd, args...)
	cmd.Dir = dir
	if v.verbose {
		fmt.Printf("cd %s\n", dir)
		fmt.Printf("%s %s\n", v.cmd, strings.Join(args, " "))
	}
	var buf bytes.Buffer
	cmd.Stdout = &buf
	cmd.Stderr = &buf
	err := cmd.Run()
	out := buf.Bytes()
	if err != nil {
		if verbose || v.verbose {
			fmt.Fprintf(os.Stderr, "# cd %s; %s %s\n", dir, v.cmd, strings.Join(args, " "))
			os.Stderr.Write(out)
		}
		return nil, err
	}
	return out, nil
}

// Ping pings to determine scheme to use.
func (v *Cmd) Ping(scheme, repo string) error {
	return v.runVerboseOnly(".", v.pingCmd, "scheme", scheme, "repo", repo)
}

// Create creates a new copy of repo in dir.
// The parent of dir must exist; dir must not.
func (v *Cmd) Create(dir, repo string) error {
	return v.run(".", v.createCmd, "dir", dir, "repo", repo)
}

// Download downloads any new changes for the repo in dir.
func (v *Cmd) Download(dir string) error {
	return v.run(dir, v.downloadCmd)
}

// Tags returns the list of available tags for the repo in dir.
func (v *Cmd) Tags(dir string) ([]string, error) {
	var tags []string
	for _, tc := range v.tagCmd {
		out, err := v.runOutput(dir, tc.cmd)
		if err != nil {
			return nil, err
		}
		re := regexp.MustCompile(`(?m-s)` + tc.pattern)
		for _, m := range re.FindAllStringSubmatch(string(out), -1) {
			tags = append(tags, m[1])
		}
	}
	return tags, nil
}

// tagSync syncs the repo in dir to the named tag,
// which either is a tag returned by tags or is v.tagDefault.
func (v *Cmd) tagSync(dir, tag string) error {
	if v.tagSyncCmd == "" {
		return nil
	}
	if tag != "" {
		for _, tc := range v.tagLookupCmd {
			out, err := v.runOutput(dir, tc.cmd, "tag", tag)
			if err != nil {
				return err
			}
			re := regexp.MustCompile(`(?m-s)` + tc.pattern)
			m := re.FindStringSubmatch(string(out))
			if len(m) > 1 {
				tag = m[1]
				break
			}
		}
	}
	if tag == "" && v.tagSyncDefault != "" {
		return v.run(dir, v.tagSyncDefault)
	}
	return v.run(dir, v.tagSyncCmd, "tag", tag)
}

// expand rewrites s to replace {k} with match[k] for each key k in match.
func expand(match map[string]string, s string) string {
	for k, v := range match {
		s = strings.Replace(s, "{"+k+"}", v, -1)
	}
	return s
}

// EOF
