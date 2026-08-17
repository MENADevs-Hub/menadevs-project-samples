# Sample Session

A walkthrough of common `todo` use cases.

## Setup

```bash
npm install
npm link   # or: node src/cli.js <command>
```

---

## Adding todos

```bash
$ todo add "Write project proposal" --project work --priority high --due 2026-07-10 --tag urgent
Added: 1cce7ca1  Write project proposal

$ todo add "Buy groceries" --project personal --tag errand
Added: d4e82afd  Buy groceries

$ todo add "Read Node.js docs" --priority low
Added: 7f3b1e22  Read Node.js docs
```

---

## Listing todos

### Default (open items only)

```bash
$ todo list
[ ] 1cce7ca1  Write project proposal [high] @work #urgent due:2026-07-10
[ ] d4e82afd  Buy groceries @personal #errand
[ ] 7f3b1e22  Read Node.js docs [low]
```

### Filter by project

```bash
$ todo list --project work
[ ] 1cce7ca1  Write project proposal [high] @work #urgent due:2026-07-10
```

### Filter by priority

```bash
$ todo list --priority low
[ ] 7f3b1e22  Read Node.js docs [low]
```

### Show overdue items

```bash
$ todo list --overdue
[ ] 9a0f4c11  Old task due:2026-01-01 OVERDUE
```

### JSON output

```bash
$ todo list --format json
[
  {
    "id": "1cce7ca1",
    "title": "Write project proposal",
    "status": "open",
    "project": "work",
    "priority": "high",
    "tags": ["urgent"],
    "due": "2026-07-10",
    ...
  }
]
```

---

## Marking done

```bash
$ todo done 1cce7ca1
Done: 1cce7ca1  Write project proposal

$ todo done 1cce          # prefix match works
Done: 1cce7ca1  Write project proposal

$ todo list --status all
[x] 1cce7ca1  Write project proposal [high] @work #urgent due:2026-07-10
[ ] d4e82afd  Buy groceries @personal #errand
[ ] 7f3b1e22  Read Node.js docs [low]
```

---

## Deleting todos

```bash
$ todo delete 7f3b1e22
Deleted: 7f3b1e22  Read Node.js docs
```

---

## Exporting

### JSON (default)

```bash
$ todo export
[
  { "id": "d4e82afd", "title": "Buy groceries", ... }
]
```

### CSV

```bash
$ todo export --format csv
id,title,status,project,priority,tags,due,created_at,completed_at
d4e82afd,"Buy groceries",open,personal,normal,errand,,2026-06-25T10:00:00.000Z,
```

### Export to file

```bash
$ todo export --format json --output backup.json
Exported 1 item(s) to backup.json
```

---

## Stats

```bash
$ todo stats
Total:    3
Open:     2
Done:     1
Overdue:  0

By project:
  personal: 1
  work: 1

By priority:
  high: 1
  normal: 1
  low: 1
```

### JSON stats

```bash
$ todo stats --format json
{
  "total": 3,
  "open": 2,
  "done": 1,
  "overdue": 0,
  "by_project": { "work": 1, "personal": 1 },
  "by_priority": { "high": 1, "normal": 1, "low": 1 }
}
```

---

## Error cases

```bash
$ todo add "Bad date" --due 2026-13-99
Error: invalid date format: '2026-13-99' (expected YYYY-MM-DD)
$ echo $?
2

$ todo done nonexistent
Error: no todo found with id: 'nonexistent'
$ echo $?
1

$ todo add "Bad priority" --priority urgent
Error: invalid priority: 'urgent' (expected low, normal, or high)
$ echo $?
2
```
