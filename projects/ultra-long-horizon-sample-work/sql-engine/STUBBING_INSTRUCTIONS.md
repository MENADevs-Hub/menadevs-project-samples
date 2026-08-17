# Skeleton Stubbing Instructions for toydb SQL Engine

You are working in the `skeleton` branch of a toydb fork. Your job is to stub out **10 specific files** in the SQL module by replacing all method/function **bodies** with `todo!()`, while keeping every type definition, struct field, enum variant, trait definition, import, derive macro, and function/method **signature** exactly intact.

## Rules

1. **Keep intact (do NOT modify):**
   - All `use` / `import` statements
   - All `struct` definitions with their exact fields and derives
   - All `enum` definitions with their exact variants and derives
   - All `trait` definitions
   - All `type` aliases
   - All `const` / `static` / `LazyLock` **declarations** (but stub their initializer bodies)
   - All `impl` block headers (including generics, lifetimes, where clauses)
   - All method/function **signatures** (name, arguments, return type, visibility, generics)
   - All associated type declarations in trait impls (e.g., `type Item = Result<Token>;`)
   - All `#[derive(...)]`, `#[cfg(test)]`, and other attributes

2. **Replace with `todo!()`:**
   - Every function body (the code between `{` and `}` of any `fn`)
   - Every `LazyLock` / static initializer body
   - The standalone `invert_remap` function body in `plan.rs`
   - The standalone `is_ident` function body in `lexer.rs`

3. **Special handling for `src/sql/mod.rs`:** Do NOT touch this file. It contains the goldenscript test runners (`SQLRunner`, `ExpressionRunner`) and module declarations. Leave it completely as-is.

4. **Verification after stubbing:**
   ```bash
   cargo check          # MUST pass — all types and signatures are intact
   cargo test --no-run  # MUST compile
   cargo test           # MUST fail — every test hits todo!()
   ```

---

## Files to Stub (10 files)

### File 1: `src/sql/parser/lexer.rs`

This file contains the `Token` enum, `Keyword` enum, `Lexer` struct, and the `is_ident` function.

**Keep all type definitions intact:**
- `pub enum Token { ... }` with all variants
- `pub enum Keyword { ... }` with all variants
- `pub struct Lexer<'a> { ... }` with its fields (iter: Peekable<Chars<'a>>)

**Stub these impl blocks (keep signatures, replace bodies with `todo!()`):**

```
impl Display for Token
  fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result → todo!()

impl From<Keyword> for Token
  fn from(keyword: Keyword) -> Self → todo!()

impl TryFrom<&str> for Keyword
  type Error = &'static str;  ← KEEP this associated type
  fn try_from(value: &str) -> std::result::Result<Self, Self::Error> → todo!()

impl Display for Keyword
  fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result → todo!()

impl Iterator for Lexer<'_>
  type Item = Result<Token>;  ← KEEP this associated type
  fn next(&mut self) -> Option<Result<Token>> → todo!()

impl<'a> Lexer<'a>
  pub fn new(input: &'a str) -> Lexer<'a> → todo!()
  fn next_if(&mut self, predicate: impl Fn(char) -> bool) -> Option<char> → todo!()
  fn next_if_map<T>(&mut self, map: impl Fn(char) -> Option<T>) -> Option<T> → todo!()
  fn next_is(&mut self, c: char) -> bool → todo!()
  fn scan(&mut self) -> Result<Option<Token>> → todo!()
  fn scan_ident_or_keyword(&mut self) -> Option<Token> → todo!()
  fn scan_ident_quoted(&mut self) -> Result<Option<Token>> → todo!()
  fn scan_number(&mut self) -> Option<Token> → todo!()
  fn scan_string(&mut self) -> Result<Option<Token>> → todo!()
  fn scan_symbol(&mut self) -> Option<Token> → todo!()
  fn skip_whitespace(&mut self) → todo!()
```

**Standalone function:**
```
pub fn is_ident(s: &str) -> bool → todo!()
```

---

### File 2: `src/sql/parser/parser.rs`

This file contains the `Parser` struct, operator enums (`PrefixOperator`, `InfixOperator`, `PostfixOperator`), the `Associativity` enum, and the `Precedence` type alias.

**Keep all type definitions intact:**
- `type Precedence = u8;`
- `enum Associativity { Left, Right }` with its variants
- `pub struct Parser<'a> { ... }` with fields
- `enum PrefixOperator { ... }` with all variants
- `enum InfixOperator { ... }` with all variants
- `enum PostfixOperator { ... }` with all variants

**Stub these impl blocks:**

```
impl Add<Associativity> for Precedence
  type Output = Self;  ← KEEP
  fn add(self, rhs: Associativity) -> Self → todo!()

impl Parser<'_>
  pub fn parse(statement: &str) -> Result<ast::Statement> → todo!()
  #[cfg(test)] pub fn parse_expr(expr: &str) -> Result<ast::Expression> → todo!()
  fn new(input: &str) -> Parser<'_> → todo!()
  fn next(&mut self) -> Result<Token> → todo!()
  fn next_ident(&mut self) -> Result<String> → todo!()
  fn next_if(&mut self, predicate: impl Fn(&Token) -> bool) -> Option<Token> → todo!()
  fn next_if_map<T>(&mut self, f: impl Fn(&Token) -> Option<T>) -> Option<T> → todo!()
  fn next_if_keyword(&mut self) -> Option<Keyword> → todo!()
  fn next_is(&mut self, token: Token) -> bool → todo!()
  fn expect(&mut self, expect: Token) -> Result<()> → todo!()
  fn skip(&mut self, token: Token) → todo!()
  fn peek(&mut self) -> Result<Option<&Token>> → todo!()
  fn parse_statement(&mut self) -> Result<ast::Statement> → todo!()
  fn parse_begin(&mut self) -> Result<ast::Statement> → todo!()
  fn parse_commit(&mut self) -> Result<ast::Statement> → todo!()
  fn parse_rollback(&mut self) -> Result<ast::Statement> → todo!()
  fn parse_explain(&mut self) -> Result<ast::Statement> → todo!()
  fn parse_create_table(&mut self) -> Result<ast::Statement> → todo!()
  fn parse_create_table_column(&mut self) -> Result<ast::Column> → todo!()
  fn parse_drop_table(&mut self) -> Result<ast::Statement> → todo!()
  fn parse_delete(&mut self) -> Result<ast::Statement> → todo!()
  fn parse_insert(&mut self) -> Result<ast::Statement> → todo!()
  fn parse_update(&mut self) -> Result<ast::Statement> → todo!()
  fn parse_select(&mut self) -> Result<ast::Statement> → todo!()
  fn parse_select_clause(&mut self) -> Result<Vec<(ast::Expression, Option<String>)>> → todo!()
  fn parse_from_clause(&mut self) -> Result<Vec<ast::From>> → todo!()
  fn parse_from_table(&mut self) -> Result<ast::From> → todo!()
  fn parse_from_join(&mut self) -> Result<Option<ast::JoinType>> → todo!()
  fn parse_where_clause(&mut self) -> Result<Option<ast::Expression>> → todo!()
  fn parse_group_by_clause(&mut self) -> Result<Vec<ast::Expression>> → todo!()
  fn parse_having_clause(&mut self) -> Result<Option<ast::Expression>> → todo!()
  fn parse_order_by_clause(&mut self) -> Result<Vec<(ast::Expression, ast::Direction)>> → todo!()
  fn parse_limit_clause(&mut self) -> Result<Option<ast::Expression>> → todo!()
  fn parse_offset_clause(&mut self) -> Result<Option<ast::Expression>> → todo!()
  fn parse_expression(&mut self) -> Result<ast::Expression> → todo!()
  fn parse_expression_at(&mut self, min_precedence: Precedence) -> Result<ast::Expression> → todo!()
  fn parse_expression_atom(&mut self) -> Result<ast::Expression> → todo!()
  fn parse_prefix_operator_at(&mut self, min_precedence: Precedence) -> Option<PrefixOperator> → todo!()
  fn parse_infix_operator_at(&mut self, min_precedence: Precedence) -> Option<InfixOperator> → todo!()
  fn parse_postfix_operator_at(&mut self, min_precedence: Precedence) -> Result<Option<PostfixOperator>> → todo!()

impl PrefixOperator
  fn precedence(&self) -> Precedence → todo!()
  fn associativity(&self) -> Associativity → todo!()
  fn into_expression(self, rhs: ast::Expression) -> ast::Expression → todo!()

impl InfixOperator
  fn precedence(&self) -> Precedence → todo!()
  fn associativity(&self) -> Associativity → todo!()
  fn into_expression(self, lhs: ast::Expression, rhs: ast::Expression) -> ast::Expression → todo!()

impl PostfixOperator
  fn precedence(&self) -> Precedence → todo!()
  fn into_expression(self, lhs: ast::Expression) -> ast::Expression → todo!()
```

---

### File 3: `src/sql/planner/planner.rs`

This file contains the `Planner` struct and the `Scope` struct.

**Keep all type definitions intact:**
- `pub struct Planner<'a, C: Catalog> { catalog: &'a C }`
- `#[derive(Default)] pub struct Scope { columns: Vec<Label>, tables: HashSet<String>, qualified: HashMap<(String, String), usize>, unqualified: HashMap<String, Vec<usize>>, aggregates: HashMap<ast::Expression, usize>, hidden: HashSet<usize> }`

**Stub these impl blocks:**

```
impl<'a, C: Catalog> Planner<'a, C>
  pub fn new(catalog: &'a C) -> Self → todo!()
  pub fn build(&mut self, statement: ast::Statement) -> Result<Plan> → todo!()
  fn build_create_table(&self, name: String, columns: Vec<ast::Column>) -> Result<Plan> → todo!()
  fn build_drop_table(&self, name: String, if_exists: bool) -> Result<Plan> → todo!()
  fn build_delete(&self, table: String, r#where: Option<ast::Expression>) -> Result<Plan> → todo!()
  fn build_insert(&self, table: String, columns: Option<Vec<String>>, values: Vec<Vec<ast::Expression>>) -> Result<Plan> → todo!()
  fn build_update(&self, table: String, set: BTreeMap<String, Option<ast::Expression>>, r#where: Option<ast::Expression>) -> Result<Plan> → todo!()
  fn build_select(&self, select: Vec<(ast::Expression, Option<String>)>, from: Vec<ast::From>, r#where: Option<ast::Expression>, group_by: Vec<ast::Expression>, having: Option<ast::Expression>, order_by: Vec<(ast::Expression, ast::Direction)>, offset: Option<ast::Expression>, limit: Option<ast::Expression>) -> Result<Plan> → todo!()
  fn build_from_clause(&self, from: Vec<ast::From>, scope: &mut Scope) -> Result<Node> → todo!()
  fn build_from(&self, from: ast::From, parent_scope: &mut Scope) -> Result<Node> → todo!()
  fn build_aggregate(&self, source: Node, group_by: Vec<ast::Expression>, aggregates: Vec<ast::Expression>, scope: &mut Scope) -> Result<Node> → todo!()
  fn build_aggregate_function(expr: ast::Expression, scope: &Scope) -> Result<Aggregate> → todo!()
  fn is_aggregate_function(expr: &ast::Expression) -> bool → todo!()
  fn collect_aggregates(select: &[(ast::Expression, Option<String>)], having: &Option<ast::Expression>, order_by: &[(ast::Expression, ast::Direction)]) -> Vec<ast::Expression> → todo!()
  fn build_select_hidden(&self, having: &Option<ast::Expression>, order_by: &[(ast::Expression, ast::Direction)], scope: &Scope, child_scope: &mut Scope) -> Vec<Expression> → todo!()
  pub fn build_expression(expr: ast::Expression, scope: &Scope) -> Result<Expression> → todo!()
  fn build_constant_value(expr: ast::Expression) -> Result<Value> → todo!()

impl Scope
  pub fn new() -> Self → todo!()
  fn from_table(table: &Table) -> Result<Self> → todo!()
  pub fn spawn(&self) -> Self → todo!()
  fn add_table(&mut self, table: &Table, alias: Option<&str>) -> Result<()> → todo!()
  fn add_column(&mut self, label: Label) -> usize → todo!()
  fn lookup_column(&self, table: Option<&str>, name: &str) -> Result<usize> → todo!()
  fn add_aggregate(&mut self, expr: &ast::Expression, parent: &Scope) -> Option<usize> → todo!()
  fn lookup_aggregate(&self, expr: &ast::Expression) -> Option<usize> → todo!()
  fn add_passthrough(&mut self, parent: &Scope, parent_index: usize, hide: bool) -> usize → todo!()
  fn merge(&mut self, scope: Scope) -> Result<()> → todo!()
  fn project(&self, expressions: &[(ast::Expression, Option<String>)]) -> Self → todo!()
  fn remap(&self, targets: &[Option<usize>]) -> Self → todo!()
  fn remove_hidden(&mut self) -> Option<HashSet<usize>> → todo!()
  fn remap_hidden(&mut self) -> Option<Vec<Option<usize>>> → todo!()
```

---

### File 4: `src/sql/planner/plan.rs`

This file contains the `Plan`, `Node`, `Aggregate`, and `Direction` enums, and the `invert_remap` function.

**Keep all type definitions intact:**
- `#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)] pub enum Plan { ... }` with all 6 variants and their fields
- `#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)] pub enum Node { ... }` with all 14 variants and their fields
- `#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)] pub enum Aggregate { ... }` with all 5 variants
- `#[derive(Clone, Copy, Debug, PartialEq, Serialize, Deserialize)] pub enum Direction { Ascending, Descending }`

**Stub these impl blocks:**

```
impl Plan
  pub fn build(statement: ast::Statement, catalog: &impl Catalog) -> Result<Self> → todo!()
  pub fn execute(self, txn: &impl Transaction) -> Result<ExecutionResult> → todo!()
  pub fn optimize(self) -> Result<Self> → todo!()

impl Node
  pub fn columns(&self) -> usize → todo!()
  pub fn column_label(&self, index: usize) -> Label → todo!()
  pub fn transform(mut self, before: &impl Fn(Self) -> Result<Self>, after: &impl Fn(Self) -> Result<Self>) -> Result<Self> → todo!()
  pub fn transform_expressions(self, before: &impl Fn(Expression) -> Result<Expression>, after: &impl Fn(Expression) -> Result<Expression>) -> Result<Self> → todo!()
  pub fn format(&self, f: &mut std::fmt::Formatter<'_>, prefix: &str, root: bool, last_child: bool) -> std::fmt::Result → todo!()

impl Aggregate
  fn format(&self, node: &Node) -> String → todo!()
  pub fn expr(&self) -> &Expression → todo!()

impl Display for Direction
  fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result → todo!()

impl From<ast::Direction> for Direction
  fn from(dir: ast::Direction) -> Self → todo!()

impl Display for Plan
  fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result → todo!()

impl Display for Node
  fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result → todo!()
```

**Standalone function:**
```
pub fn invert_remap(targets: &[Option<usize>]) -> Vec<Option<usize>> → todo!()
```

---

### File 5: `src/sql/planner/optimizer.rs`

This file contains the `Optimizer` trait, 5 optimizer structs, and the `OPTIMIZERS` static.

**Keep all type definitions intact:**
- `pub trait Optimizer: Debug + Send + Sync { fn optimize(&self, node: Node) -> Result<Node>; }`
- `#[derive(Debug)] struct ConstantFolding;`
- `#[derive(Debug)] struct FilterPushdown;`
- `#[derive(Debug)] struct IndexLookup;`
- `#[derive(Debug)] struct HashJoin;`
- `#[derive(Debug)] struct ShortCircuit;`

**Keep the OPTIMIZERS static declaration but stub its initializer:**
```rust
pub static OPTIMIZERS: LazyLock<Vec<Box<dyn Optimizer>>> = LazyLock::new(|| {
    todo!()
});
```

**Stub these impl blocks:**

```
impl Optimizer for ConstantFolding
  fn optimize(&self, node: Node) -> Result<Node> → todo!()

impl ConstantFolding
  pub fn fold(mut expr: Expression) -> Result<Expression> → todo!()

impl Optimizer for FilterPushdown
  fn optimize(&self, node: Node) -> Result<Node> → todo!()

impl FilterPushdown
  fn push_filters(mut node: Node) -> Node → todo!()
  fn push_into(expr: Expression, target: &mut Node) -> Option<Expression> → todo!()
  fn maybe_push_filter(node: Node) -> Node → todo!()
  fn maybe_push_join(node: Node) -> Node → todo!()

impl Optimizer for IndexLookup
  fn optimize(&self, node: Node) -> Result<Node> → todo!()

impl IndexLookup
  fn index_lookup(mut node: Node) -> Node → todo!()

impl Optimizer for HashJoin
  fn optimize(&self, node: Node) -> Result<Node> → todo!()

impl HashJoin
  pub fn hash_join(node: Node) -> Node → todo!()

impl Optimizer for ShortCircuit
  fn optimize(&self, node: Node) -> Result<Node> → todo!()

impl ShortCircuit
  fn short_circuit(mut node: Node) -> Node → todo!()
```

---

### File 6: `src/sql/execution/executor.rs`

This file contains the `Executor` struct and `ExecutionResult` enum.

**Keep all type definitions intact:**
- `pub struct Executor<'a, T: Transaction> { txn: &'a T }`
- `pub enum ExecutionResult { CreateTable { name: String }, DropTable { name: String, existed: bool }, Delete { count: u64 }, Insert { count: u64 }, Update { count: u64 }, Select { columns: Vec<Label>, rows: Rows } }`

**Stub these impl blocks:**

```
impl<'a, T: Transaction> Executor<'a, T>
  pub fn new(txn: &'a T) -> Self → todo!()
  pub fn execute(&mut self, plan: Plan) -> Result<ExecutionResult> → todo!()
  fn execute_node(&mut self, node: Node) -> Result<Rows> → todo!()
  fn delete(&self, table: &str, primary_key: usize, source: Rows) -> Result<u64> → todo!()
  fn insert(&self, table: Table, column_map: Option<HashMap<usize, usize>>, mut source: Rows) -> Result<u64> → todo!()
  fn update(&self, table: &str, primary_key: usize, mut source: Rows, expressions: Vec<(usize, Expression)>) -> Result<u64> → todo!()
  fn order(source: Rows, order: Vec<(Expression, Direction)>) -> Result<Rows> → todo!()
```

---

### File 7: `src/sql/execution/session.rs`

This file contains the `Session` struct, `StatementResult` enum, and many `TryFrom` impls.

**Keep all type definitions intact:**
- `pub struct Session<'a, E: Engine<'a>> { ... }` with all its fields (engine, txn)
- `pub enum StatementResult { Begin(...), Commit {...}, Rollback {...}, Explain(...), CreateTable {...}, DropTable {...}, Delete {...}, Insert {...}, Update {...}, Select {...} }` with all variants and their exact fields

**Stub these impl blocks:**

```
impl<'a, E: Engine<'a>> Session<'a, E>
  pub fn new(engine: &'a E) -> Self → todo!()
  pub fn execute(&mut self, statement: &str) -> Result<StatementResult> → todo!()
  pub fn with_txn<F, T>(&mut self, read_only: bool, f: F) -> Result<T>
    where F: FnOnce(&mut E::Transaction) -> Result<T> → todo!()

impl Session<'_, Raft>
  pub fn status(&self) -> Result<Status> → todo!()

impl<'a, E: Engine<'a>> Drop for Session<'a, E>
  fn drop(&mut self) → todo!()

impl TryFrom<ExecutionResult> for StatementResult
  type Error = Error;  ← KEEP
  fn try_from(result: ExecutionResult) -> Result<Self> → todo!()

impl TryFrom<StatementResult> for Rows
  type Error = Error;  ← KEEP
  fn try_from(result: StatementResult) -> Result<Self> → todo!()

impl TryFrom<StatementResult> for Row
  type Error = Error;  ← KEEP
  fn try_from(result: StatementResult) -> Result<Self> → todo!()

impl TryFrom<StatementResult> for Value
  type Error = Error;  ← KEEP
  fn try_from(result: StatementResult) -> Result<Self> → todo!()

impl TryFrom<StatementResult> for bool
  type Error = Error;  ← KEEP
  fn try_from(result: StatementResult) -> Result<Self> → todo!()

impl TryFrom<StatementResult> for f64
  type Error = Error;  ← KEEP
  fn try_from(result: StatementResult) -> Result<Self> → todo!()

impl TryFrom<StatementResult> for i64
  type Error = Error;  ← KEEP
  fn try_from(result: StatementResult) -> Result<Self> → todo!()

impl TryFrom<StatementResult> for String
  type Error = Error;  ← KEEP
  fn try_from(result: StatementResult) -> Result<Self> → todo!()
```

---

### File 8: `src/sql/execution/aggregator.rs`

This file contains the `Aggregator` struct and the `Accumulator` enum.

**Keep all type definitions intact:**
- `pub struct Aggregator { group_by: Vec<Expression>, aggregates: Vec<Aggregate>, buckets: BTreeMap<Vec<Value>, Vec<Accumulator>> }`
- `#[derive(Clone)] enum Accumulator { Average { count: i64, sum: Value }, Count(i64), Max(Option<Value>), Min(Option<Value>), Sum(Option<Value>) }`

**Stub these impl blocks:**

```
impl Aggregator
  pub fn new(group_by: Vec<Expression>, aggregates: Vec<Aggregate>) -> Self → todo!()
  pub fn add(&mut self, row: &Row) -> Result<()> → todo!()
  pub fn add_rows(&mut self, rows: Rows) -> Result<()> → todo!()
  pub fn into_rows(self) -> Rows → todo!()

impl Accumulator
  fn new(aggregate: &Aggregate) -> Self → todo!()
  fn add(&mut self, value: Value) -> Result<()> → todo!()
  fn value(self) -> Result<Value> → todo!()
```

---

### File 9: `src/sql/execution/join.rs`

This file contains the `NestedLoopJoiner` and `HashJoiner` structs.

**Keep all type definitions intact:**
- `#[derive(Clone)] pub struct NestedLoopJoiner { left: Peekable<Rows>, right: Rows, right_original: Rows, right_columns: usize, right_matched: bool, predicate: Option<Expression>, outer: bool }`
- `#[derive(Clone)] pub struct HashJoiner { left: Rows, left_column: usize, right: HashMap<Value, Vec<Row>>, right_columns: usize, outer: bool, pending: Rows }`

**Stub these impl blocks:**

```
impl NestedLoopJoiner
  pub fn new(left: Rows, right: Rows, right_columns: usize, predicate: Option<Expression>, outer: bool) -> Self → todo!()
  fn try_next(&mut self) -> Result<Option<Row>> → todo!()

impl Iterator for NestedLoopJoiner
  type Item = Result<Row>;  ← KEEP
  fn next(&mut self) -> Option<Self::Item> → todo!()

impl HashJoiner
  pub fn new(left: Rows, left_column: usize, mut right: Rows, right_column: usize, right_columns: usize, outer: bool) -> Result<Self> → todo!()
  fn try_next(&mut self) -> Result<Option<Row>> → todo!()

impl Iterator for HashJoiner
  type Item = Result<Row>;  ← KEEP
  fn next(&mut self) -> Option<Self::Item> → todo!()
```

---

### File 10: `src/sql/engine/local.rs`

This file contains the `Key` enum, `KeyPrefix` enum, `Local` struct, and `Transaction` struct.

**Keep all type definitions intact:**
- `pub enum Key<'a> { Table(Cow<'a, str>), Index(Cow<'a, str>, Cow<'a, str>, Cow<'a, Value>), Row(Cow<'a, str>, Cow<'a, Value>) }` with its derive macros
- `enum KeyPrefix<'a> { Table, Index(Cow<'a, str>, Cow<'a, str>), Row(Cow<'a, str>) }` with its derive macros
- `pub struct Local<E: storage::Engine + 'static> { pub mvcc: mvcc::MVCC<E> }`
- `pub struct Transaction<E: storage::Engine + 'static> { txn: mvcc::Transaction<E> }`

**Keep encoding trait impls as-is** (these likely use derive macros or have default implementations):
- `impl<'a> encoding::Key<'a> for Key<'a>` — if this has a custom body, stub it; if it's derived/default, keep it
- `impl<'a> encoding::Key<'a> for KeyPrefix<'a>` — same

**Stub these impl blocks:**

```
impl<E: storage::Engine> Local<E>
  pub fn new(engine: E) -> Self → todo!()
  pub fn resume(&self, state: mvcc::TransactionState) -> Result<Transaction<E>> → todo!()
  pub fn get_unversioned(&self, key: &[u8]) -> Result<Option<Vec<u8>>> → todo!()
  pub fn set_unversioned(&self, key: &[u8], value: Vec<u8>) -> Result<()> → todo!()

impl<E: storage::Engine> super::Engine<'_> for Local<E>
  type Transaction = Transaction<E>;  ← KEEP
  fn begin(&self) -> Result<Self::Transaction> → todo!()
  fn begin_read_only(&self) -> Result<Self::Transaction> → todo!()
  fn begin_as_of(&self, version: mvcc::Version) -> Result<Self::Transaction> → todo!()

impl<E: storage::Engine> Transaction<E>
  fn new(txn: mvcc::Transaction<E>) -> Self → todo!()
  pub fn state(&self) -> &mvcc::TransactionState → todo!()
  fn get_index(&self, table: &str, column: &str, value: &Value) -> Result<BTreeSet<Value>> → todo!()
  fn get_row(&self, table: &str, id: &Value) -> Result<Option<Row>> → todo!()
  fn has_index(&self, table: &str, column: &str) -> Result<bool> → todo!()
  fn set_index(&self, table: &str, column: &str, value: &Value, ids: BTreeSet<Value>) -> Result<()> → todo!()
  fn table_references(&self, table: &str) -> Result<Vec<(Table, Vec<usize>)>> → todo!()

impl<E: storage::Engine> super::Transaction for Transaction<E>
  fn state(&self) -> &mvcc::TransactionState → todo!()
  fn commit(self) -> Result<()> → todo!()
  fn rollback(self) -> Result<()> → todo!()
  fn delete(&self, table: &str, ids: &[Value]) -> Result<()> → todo!()
  fn get(&self, table: &str, ids: &[Value]) -> Result<Vec<Row>> → todo!()
  fn insert(&self, table: &str, rows: Vec<Row>) -> Result<()> → todo!()
  fn lookup_index(&self, table: &str, column: &str, values: &[Value]) -> Result<BTreeSet<Value>> → todo!()
  fn scan(&self, table: &str, filter: Option<Expression>) -> Result<Rows> → todo!()
  fn update(&self, table: &str, rows: BTreeMap<Value, Row>) -> Result<()> → todo!()

impl<E: storage::Engine> Catalog for Transaction<E>
  fn create_table(&self, table: Table) -> Result<()> → todo!()
  fn drop_table(&self, table: &str, if_exists: bool) -> Result<bool> → todo!()
  fn get_table(&self, table: &str) -> Result<Option<Table>> → todo!()
  fn list_tables(&self) -> Result<Vec<Table>> → todo!()
```

---

## How to Apply

For each of the 10 files above:

1. Open the file
2. For every `fn` inside an `impl` block or at module level:
   - Keep the full signature line(s) exactly as they are
   - Replace everything between the opening `{` and closing `}` of the function body with just `todo!()`
3. For the `OPTIMIZERS` static in `optimizer.rs`:
   - Keep `pub static OPTIMIZERS: LazyLock<Vec<Box<dyn Optimizer>>> = LazyLock::new(|| {`
   - Replace the body with `todo!()`
   - Keep `});`
4. Keep ALL `type Error = ...;` and `type Item = ...;` and `type Transaction = ...;` associated type declarations
5. Keep ALL `use` statements at the top of the file
6. Keep ALL struct/enum/trait definitions with their fields, variants, and derive macros

## Example Transformation

**Before:**
```rust
pub fn new(engine: E) -> Self {
    Self { mvcc: mvcc::MVCC::new(engine) }
}
```

**After:**
```rust
pub fn new(engine: E) -> Self {
    todo!()
}
```

**Before (multi-line body):**
```rust
fn scan(&self, table: &str, filter: Option<Expression>) -> Result<Rows> {
    let table = self.must_get_table(table)?;
    let rows = /* ... long implementation ... */;
    Ok(rows)
}
```

**After:**
```rust
fn scan(&self, table: &str, filter: Option<Expression>) -> Result<Rows> {
    todo!()
}
```

## Post-Stubbing Verification

After all 10 files are stubbed, run:

```bash
cargo check
```

If `cargo check` fails, it means a type definition or signature was accidentally modified. Fix any compilation errors while ensuring all method bodies remain `todo!()`.

Then run:

```bash
cargo test --no-run
```

This should compile but not execute. Then:

```bash
cargo test 2>&1 | head -50
```

This should show test failures from `todo!()` panics, confirming the skeleton is correctly set up.
