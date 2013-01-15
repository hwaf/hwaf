package main

import (
	"fmt"
	"os"
	"os/exec"
	// "path/filepath"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
	"github.com/sbinet/go-svn2git/svn"
)

func hwaf_make_cmd_git_svn_clone() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_git_svn_clone,
		UsageLine: "svn-clone [options] <URL>",
		Short:     "convert a SVN repository into a GIT one",
		Long: `
svn-clone converts a SVN repository into a GIT one.

ex:
 $ hwaf git svn-clone svn+ssh://svn.cern.ch/atlasoff/Control/AthenaCommon
`,
		Flag: *flag.NewFlagSet("hwaf-git-svn-clone", flag.ExitOnError),
	}
	cmd.Flag.Bool("verbose", false, "")
	cmd.Flag.Bool("metadata", false, "include metadata in git logs (git-svn-id)")
	cmd.Flag.Bool("no-minimize-url", false, "accept URLs as-is without attempting to connect a higher level directory")
	cmd.Flag.Bool("root-is-trunk", false, "use this if the root level of the repo is equivalent to the trunk and there are no tags or branches")
	cmd.Flag.Bool("rebase", false, "instead of cloning a new project, rebase an existing one against SVN")
	cmd.Flag.String("username", "", "username for transports that needs it (http(s), svn)")
	cmd.Flag.String("trunk", "trunk", "subpath to trunk from repository URL")
	cmd.Flag.String("branches", "branches", "subpath to branches from repository URL")
	cmd.Flag.String("tags", "tags", "subpath to tags from repository URL")
	cmd.Flag.String("exclude", "", "regular expression to filter paths when fetching")
	cmd.Flag.String("revision", "", "start importing from SVN revision START_REV; optionally end at END_REV. e.g. -revision START_REV:END_REV")

	cmd.Flag.Bool("no-trunk", false, "do not import anything from trunk")
	cmd.Flag.Bool("no-branches", false, "do not import anything from branches")
	cmd.Flag.Bool("no-tags", false, "do not import anything from tags")
	cmd.Flag.String("authors", "$HOME/.config/go-svn2git/authors", "path to file containing svn-to-git authors mapping")
	return cmd
}

func hwaf_run_cmd_git_svn_clone(cmd *commander.Command, args []string) {
	var err error
	n := "hwaf-" + cmd.Name()

	ctx := svn.NewContextFrom(
		"no-url",
		cmd.Flag.Lookup("verbose").Value.Get().(bool),
		cmd.Flag.Lookup("metadata").Value.Get().(bool),
		cmd.Flag.Lookup("no-minimize-url").Value.Get().(bool),
		cmd.Flag.Lookup("root-is-trunk").Value.Get().(bool),
		cmd.Flag.Lookup("rebase").Value.Get().(bool),
		cmd.Flag.Lookup("username").Value.Get().(string),
		cmd.Flag.Lookup("trunk").Value.Get().(string),
		cmd.Flag.Lookup("branches").Value.Get().(string),
		cmd.Flag.Lookup("tags").Value.Get().(string),
		cmd.Flag.Lookup("exclude").Value.Get().(string),
		cmd.Flag.Lookup("revision").Value.Get().(string),
		cmd.Flag.Lookup("no-trunk").Value.Get().(bool),
		cmd.Flag.Lookup("no-branches").Value.Get().(bool),
		cmd.Flag.Lookup("no-tags").Value.Get().(bool),
		cmd.Flag.Lookup("authors").Value.Get().(string),
	)

	if ctx.RootIsTrunk {
		ctx.Trunk = ""
		ctx.Branches = ""
		ctx.Tags = ""
	}

	if ctx.NoTrunk {
		ctx.Trunk = ""
	}

	if ctx.NoBranches {
		ctx.Branches = ""
	}

	if ctx.NoTags {
		ctx.Tags = ""
	}

	if ctx.Verbose {
		fmt.Printf("==go-svn2git...\n")
		fmt.Printf(" verbose:  %v\n", ctx.Verbose)
		fmt.Printf(" rebase:   %v\n", ctx.Rebase)
		fmt.Printf(" username: %q\n", ctx.UserName)
		fmt.Printf(" trunk:    %q\n", ctx.Trunk)
		fmt.Printf(" branches: %q\n", ctx.Branches)
		fmt.Printf(" tags:     %q\n", ctx.Tags)
		fmt.Printf(" authors:  %q\n", ctx.Authors)
		fmt.Printf(" root-is-trunk: %v\n", ctx.RootIsTrunk)
		fmt.Printf(" exclude:  %q\n", ctx.Exclude)
	}

	if ctx.Rebase {
		if len(args) > 0 {
			fmt.Printf("%s: too many arguments\n", n)
			fmt.Printf("%s: \"-rebase\" takes no argument\n", n)
			//git_svn_usage()
			git := exec.Command("git", "status", "--porcelain", "--untracked-files=no")
			out, err := git.CombinedOutput()
			if len(out) != 0 {
				fmt.Printf("%s: you have pending changes. The working tree must be clean in order to continue.\n", n)
			}
			handle_err(err)
		}
	} else {
		ok := true
		switch len(args) {
		case 0:
			fmt.Printf("%s: missing SVN_URL parameter\n", n)
			ok = false
		case 1:
			/*noop*/
		default:
			fmt.Printf("%s: too many arguments: %v\n", n, args)
			fmt.Printf("%s: did you pass an option *after* the url ?\n", n)
			ok = false
		}
		if !ok {
			fmt.Printf("%s: \"-help\" for help\n", n)
			os.Exit(1)
		}
		ctx.Url = args[0]
	}

	err = ctx.Run()
	handle_err(err)
}

// EOF
