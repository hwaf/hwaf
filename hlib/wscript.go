package hlib

type Wscript_t struct {
	Package   Package_t
	Options   Options_t
	Configure Configure_t
	Build     Build_t
}

type Stmt interface {
	is_stmt()
}

type Package_t struct {
	Name     string
	Authors  []Author
	Managers []Manager
	Version  Version
	Deps     []Dep_t
}

type Author string
type Manager string
type Version string

type Dep_t struct {
	Name    string
	Version string
	Type    DepType
}

type DepType int

const (
	PublicDep DepType = iota << 1
	PrivateDep
	RuntimeDep
)

type Visibility int

const (
	Local    Visibility = 0
	Exported Visibility = 1
)

type Options_t struct {
	Tools    []string
	HwafCall []string
	Stmts    []Stmt
}

type Configure_t struct {
	Tools    []string
	HwafCall []string
	Env      Env_t
	//Tags  []Value
	Stmts []Stmt
}

type Env_t map[string]Value

type Build_t struct {
	Tools    []string
	HwafCall []string
	Targets  Targets_t
	Stmts    []Stmt
	Env      Env_t
}

type Targets_t []Target_t

type Target_t struct {
	Name           string
	Features       string
	Source         []Value
	Use            []Value
	Defines        []Value
	CFlags         []Value
	CxxFlags       []Value
	LinkFlags      []Value
	ShlibFlags     []Value
	StlibFlags     []Value
	RPath          []Value
	Includes       []Value
	ExportIncludes []Value
}

type KeyValue struct {
	Tag   string
	Value []string
}

type Value struct {
	Name string
	Set  []KeyValue // first item is the "default"
}

// EOF
