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
	Version Version
	Type    DepType
}

type DepType int

const (
	UnknownDep DepType = 1 << iota
	PublicDep
	PrivateDep
	RuntimeDep
)

func (d DepType) HasMask(mask DepType) bool {
	return bool((d & mask) != 0)
}

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
	Features       []string
	Source         []Value
	Target         string
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
	InstallPath    []Value
	KwArgs         map[string][]Value
}

// make Targets_t sortable

func (tgts Targets_t) Len() int           { return len(tgts) }
func (tgts Targets_t) Less(i, j int) bool { return tgts[i].Name < tgts[j].Name }
func (tgts Targets_t) Swap(i, j int)      { tgts[i], tgts[j] = tgts[j], tgts[i] }

type KeyValue struct {
	Tag   string
	Value []string
}

type Value struct {
	Name string
	Set  []KeyValue // first item is the "default"
}

// EOF
