# Sample Session

A walkthrough of the most common `dirtree` use cases against a small project directory.

## Setup

```
$ ls project/
README.md  src/  tests/  node_modules/  .git/
```

---

## tree command

### Basic tree

```
$ dirtree tree project/
project/
├── src/
│   ├── cli.js
│   ├── summary.js
│   ├── tree.js
│   └── utils.js
├── tests/
│   ├── summary.test.js
│   ├── tree.test.js
│   └── utils.test.js
├── node_modules/
└── README.md
```

### Limit depth

```
$ dirtree tree project/ --depth 1
project/
├── src/
├── tests/
├── node_modules/
└── README.md
```

### Exclude patterns

```
$ dirtree tree project/ --ignore node_modules --ignore .git
project/
├── src/
│   ├── cli.js
│   ├── summary.js
│   ├── tree.js
│   └── utils.js
├── tests/
│   ├── summary.test.js
│   ├── tree.test.js
│   └── utils.test.js
└── README.md
```

### Show file sizes

```
$ dirtree tree project/ --ignore node_modules --size
project/
├── src/
│   ├── cli.js (1.8 KB)
│   ├── summary.js (2.4 KB)
│   ├── tree.js (4.6 KB)
│   └── utils.js (1.3 KB)
├── tests/
│   ├── summary.test.js (2.1 KB)
│   ├── tree.test.js (3.0 KB)
│   └── utils.test.js (1.8 KB)
└── README.md (3.2 KB)
```

### Include hidden files

```
$ dirtree tree project/ --ignore node_modules --hidden --depth 1
project/
├── .git/
├── src/
├── tests/
└── README.md
```

### JSON output

```
$ dirtree tree project/ --ignore node_modules --depth 1 --format json
{
  "name": "project",
  "type": "directory",
  "children": [
    { "name": "src", "type": "directory", "children": [] },
    { "name": "tests", "type": "directory", "children": [] },
    { "name": "README.md", "type": "file", "size": 3274 }
  ]
}
```

---

## summary command

### Basic summary

```
$ dirtree summary project/ --ignore node_modules
Directory:   /home/user/project
Files:       7
Directories: 2
Total size:  20.2 KB
```

### Limit depth

```
$ dirtree summary project/ --ignore node_modules --depth 1
Directory:   /home/user/project
Files:       1
Directories: 2
Total size:  3.2 KB
```

### JSON output

```
$ dirtree summary project/ --ignore node_modules --format json
{
  "path": "/home/user/project",
  "files": 7,
  "directories": 2,
  "total_size": 20685,
  "total_size_human": "20.2 KB"
}
```

---

## Error cases

### Non-existent path

```
$ dirtree tree /no/such/path
Error: path does not exist: /no/such/path
$ echo $?
1
```

### Permission denied (walk continues)

```
$ dirtree tree /var/protected/
/var/protected/
Warning: cannot read directory /var/protected/secret: permission denied
└── public.txt
```

### Invalid depth

```
$ dirtree tree . --depth bad
Error: --depth must be a non-negative integer
$ echo $?
2
```
