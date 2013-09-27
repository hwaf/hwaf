hwaf
====

[![Build Status](https://drone.io/github.com/hwaf/hwaf/status.png)](https://drone.io/github.com/hwaf/hwaf/latest)

``hwaf`` is a set of commands to ease developing against and with
``waf`` based projects, in High Energy Physics software.

``hwaf`` is a ``Go`` binary produce by the [Go toolchain](http://golang.org)

It is very much like [Git](https://github.com/git) in the sense that
it is a multi sub-command binary with the ability to extend its
functionalities via third-party sub-commands.

The typical workflow of somebody developing against some project:

```sh
# initialize hwaf. this has to be done the first time you install hwaf
hwaf self init

# initialize a local workarea
hwaf init work
cd work

# setup hwaf to use a given project
# the directory given to hwaf needs to hold a special
# 'project.info' metadata file
hwaf setup -p /opt/sw/mana/mana-core/<vers>/<variant>


# checkout a few packages
hwaf pkg co git://github.com/mana-fwk/mana-core-athenakernel Control/AthenaKernel
hwaf pkg co git://github.com/mana-fwk/mana-core-gaudikernel GaudiKernel

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

    asetup      setup a workarea with Athena-like defaults
    init        initialize a new workarea
    setup       setup an existing workarea
    version     print version and exit
    waf         run waf itself
    configure   configure local project or packages
    build       build local project or packages
    check       build and run unit-tests for the local project or packages
    install     install local project or packages
    clean       clean local project or packages
    distclean   distclean local project or packages
    shell       run an interactive shell with the correct environment
    run         run a command with the correct (project) environment
    sdist       create a source distribution from the project or packages
    bdist       create a binary distribution from the project or packages
    bdist-deb   create a DEB from the local project/packages
    bdist-rpm   create a RPM from the local project/packages
    dump-env    print the environment on STDOUT

    git         hwaf related git tools
    pkg         add, remove or inspect sub-packages
    show        show informations about packages and projects
    pmgr        query, download and install projects
    self        modify hwaf internal state

Use "hwaf help [command]" for more information about a command.

Additional help topics:


Use "hwaf help [topic]" for more information about that topic.
```


## Installation

There are 2 ways to install ``hwaf``.

### Installation using the ``Go`` toolchain

``hwaf`` is a ``Go`` binary produced by the
[Go toolchain](http://golang.org).
If you haven't already a ``Go`` toolchain installed, you may want to
look [here](http://golang.org/doc/install.html) for the detailed
instructions.
But a quick getting started guide could be:

```sh
# get the Go toolchain
$ curl -L -O https://code.google.com/go/downloads/....
# unpack somewhere, say, /usr/local/go
$ export GOROOT=/usr/local/go
$ export PATH=$GOROOT/bin:$PATH
$ which go
/usr/local/go/bin/go

# setup a development environment
$ export GOPATH=$HOME/gocode
$ export PATH=$GOPATH/bin:$PATH
```

then, you just have to do:

```sh
$ go get github.com/hwaf/hwaf
```

to get the latest ``hwaf`` tool installed (under
``$GOPATH/src/github.com/hwaf/hwaf``) and ready.


### Installation from binaries

Packaged up binaries for ``hwaf`` are also available [here](http://cern.ch/mana-fwk/downloads/tar).
Untar under some directory like so (for linux 64b):

```sh
$ mkdir local
$ cd local
$ curl -L \
  http://cern.ch/mana-fwk/downloads/tar/hwaf-20130926-linux-amd64.tar.gz \
  | tar zxf -
$ export HWAF_ROOT=`pwd`
$ export PATH=$HWAF_ROOT/bin:$PATH
```

If you are at CERN, binaries are installed here:

```sh
$ . /afs/cern.ch/atlas/project/hwaf/sw/install/hwaf-20130926/linux-amd64/setup-hwaf.sh
```
