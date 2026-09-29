# Stremio library API (unofficial)

Stremio has no public documentation for its user API. These notes come from
Stremio's own client, [stremio-core](https://github.com/Stremio/stremio-core)
(checked at commit `88be65b`, 2026-09-24). The API can change without notice.

## Basics

* Base URL: `https://api.strem.io/api/`
* Every call is a `POST` with a JSON body
* Responses are either `{"result": ...}` or `{"error": {"message": "...", "code": 1}}`

## Authentication

Log in once to get an `authKey` (a long-lived session key). Only the key is
stored for this project, never the password. The key stays valid until the
session is logged out.

```
POST https://api.strem.io/api/login
{"type": "Login", "email": "...", "password": "...", "facebook": false}

-> {"result": {"authKey": "...", "user": {...}}}
```

## Reading the library

```
POST https://api.strem.io/api/datastoreGet
{"authKey": "...", "collection": "libraryItem", "ids": [], "all": true}

-> {"result": [LibraryItem, ...]}
```

`ids: []` with `all: true` returns every item.

## LibraryItem fields used here

| Field | Meaning |
| --- | --- |
| `_id` | Item ID; the IMDb ID (`tt...`) for movies and series from Cinemeta |
| `name` | Title as shown in Stremio (usually English) |
| `type` | `movie`, `series`, or `other` |
| `poster` | Poster URL |
| `removed` | `true` when the item is not in the library |
| `temp` | `true` for items that were only watched, not saved |
| `_mtime` | Last modification time |
| `state` | Watch progress (not used here) |

## Which items count as "in the library"

Stremio's Library screen shows items with `removed == false`
(`NotRemovedFilter` in `src/models/library_with_filters.rs`). Items that were
only played without being saved are stored too, with `temp: true`, and appear
only in Continue Watching.

This project syncs items where:

* `removed` is `false`
* `type` is `movie` or `series`
* `_id` starts with `tt`