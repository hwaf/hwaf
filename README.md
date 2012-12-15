hwaf
====

``hwaf`` is a set of commands to ease developing against and with
``waf`` based projects, in High Energy Physics software.

``hwaf`` is a ``Go`` binary produce by the [Go toolchain](http://golang.org)

It is very much like [Git](https://github.com/git) in the sense that
it is a multi sub-command binary with the ability to extend its
functionalities via third-party sub-commands.

The typical workflow of somebody developing against some project:

```sh
# initialize hwaf. this has to be done the first time you install hwaf
hwaf self-init

# initialize a local workarea
hwaf init work
cd work

# setup hwaf to use a given project
# the directory given to hwaf needs to hold a special
# 'project.info' metadata file
hwaf setup -p /opt/sw/mana/mana-core/<vers>/<cmtcfg>


# checkout a few packages
hwaf co git://github.com/mana-fwk/mana-core-athenakernel Control/AthenaKernel
hwaf co git://github.com/mana-fwk/mana-core-gaudikernel GaudiKernel

# configure (every time a new package has been added)
hwaf configure

# build+install
hwaf
hwaf install

# run a command from the build or the parent project(s)
hwaf run my-command --verbose

# spawn a sub-shell to run a command from the build or parent
# project(s)
# exit with ^D
hwaf shell
my-command --verbose
^D

# when in doubt, you can always get some help:
$ hwaf help
Usage:

		hwaf command [arguments]

The commands are:

    init        initialize a new workarea
    setup       setup an existing workarea
    co          add a package to the current workarea
    version     print version and exit
    self-init   initialize hwaf itself
    self-update update hwaf itself
    waf         run waf itself
    configure   configure local project or packages
    build       build local project or packages
    install     install local project or packages
    clean       clean local project or packages
    distclean   distclean local project or packages
    shell       run an interactive shell with the correct environment
    run         run a command with the correct (project) environment
    show-projects show local project dependencies
    show-pkg-uses show local project dependencies

Use "hwaf help [command]" for more information about a command.

Additional help topics:


Use "hwaf help [topic]" for more information about that topic.


```





