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

//
// ----------- cmt statements models ----------
//

// PathStmt declares a new path entry with name Name and value Value
type PathStmt struct {
	Value Value
}

func (stmt *PathStmt) is_stmt() {
}

type PathAppendStmt struct {
	Value Value
}

func (stmt *PathAppendStmt) is_stmt() {
}

type PathPrependStmt struct {
	Value Value
}

func (stmt *PathPrependStmt) is_stmt() {
}

type PathRemoveStmt struct {
	Value Value
}

func (stmt *PathRemoveStmt) is_stmt() {
}

type MacroStmt struct {
	Value Value
}

func (stmt *MacroStmt) is_stmt() {
}

type MacroAppendStmt struct {
	Value Value
}

func (stmt *MacroAppendStmt) is_stmt() {
}

type MacroRemoveStmt struct {
	Value Value
}

func (stmt *MacroRemoveStmt) is_stmt() {
}

// TagStmt defines a new CMT tag with name Name and content Content
type TagStmt struct {
	Name    string
	Content []string
}

func (stmt *TagStmt) is_stmt() {
}

type IncludeDirsStmt struct {
	Value []string
}

func (stmt *IncludeDirsStmt) is_stmt() {
}

type IncludePathStmt struct {
	Value []string
}

func (stmt *IncludePathStmt) is_stmt() {
}

type SetStmt struct {
	Value Value
}

func (stmt *SetStmt) is_stmt() {
}

type AliasStmt struct {
	Value Value
}

func (stmt *AliasStmt) is_stmt() {
}

// test interfaces
var _ Stmt = (*PathStmt)(nil)
var _ Stmt = (*PathAppendStmt)(nil)
var _ Stmt = (*PathPrependStmt)(nil)
var _ Stmt = (*PathRemoveStmt)(nil)
var _ Stmt = (*MacroStmt)(nil)
var _ Stmt = (*MacroAppendStmt)(nil)
var _ Stmt = (*MacroRemoveStmt)(nil)
var _ Stmt = (*TagStmt)(nil)
var _ Stmt = (*IncludeDirsStmt)(nil)
var _ Stmt = (*IncludePathStmt)(nil)
var _ Stmt = (*SetStmt)(nil)
var _ Stmt = (*AliasStmt)(nil)

// EOF
