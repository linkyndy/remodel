# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2019-06-11
### Added
- custom table names for models, using `Model.table_name` (#48, #63, thank you, @arwema!)
- filter models by lambda, using `Model.filter(lambda x: x)` (#66)
- support RethinkDB's new user/password authentication (#65, thank you, @caj-larsson!)
- support for Python 3.6 and 3.7 (#61)

### Changed
- support for `rethinkdb>=2.4` package (#60)
- fix invalid references when deleting an object (#55, thank you @jspalink!)

### Removed
- deprecated functions from `remodel.utils` (#62)
- deprecated `Model._table` (#63)

## [0.4.4] - 2015-11-21
### Added
- support for Python 3.5 (#36, thank you, @thedrow!)

### Changed
- fix circular import when registering a model (#39, thank you, @JannKleen!)

## [0.4.3] - 2015-08-31
### Changed
- do not trigger validations when wrapping a document returned by `ObjectHandler` (#25, thank you, @derkan!)
- wait for indexes to be created in `create_indexes()`
- use Travis CI

## [0.4.2] - 2015-05-23
### Changed
- use `return_changes='always'` to always return changes, even when the document hasn’t been modified

## [0.4.1] - 2015-05-12
### Changed
- fix for RethinkDB 2.0's API change related to `changes`

## [0.4.0] - 2015-03-14
### Added
- implement callbacks for running custom behaviour before/after saving/deleting/initializing an object
- `get()` and `update()` methods to objects
- move `create_tables()` and `create_indexes()` from `remodel.utils` to `remodel.helpers`
- new helper `drop_tables()`

### Changed
- `create_tables()` can be run multiple times now
- fix secondary index for belongs_to relation
- use `inflection.tableize` instead of homegrown variant
- improve index creation in `create_indexes()`

## [0.3.1] - 2015-02-13
### Changed
- fix `create_tables()` following an API change on `r.table_create()` (thank you, @Gesias!)

## [0.3.0] - 2015-01-23
### Added
- support for Python 3.4 (#9, thank you, @bmjjr!)

## [0.2.0] - 2014-12-15
### Added
- introduce `ObjectHandler`, which exposes table-related operations on the `Model`

### Changed
- swap `inflect` module for `inflection`
- improve error handling in `create_tables()` and `create_indexes()`

## [0.1.0] - 2014-12-07
- remodel's inception <3

[Unreleased]: https://github.com/linkyndy/pallets/compare/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/linkyndy/pallets/compare/v0.4.4...v1.0.0
[0.4.4]: https://github.com/linkyndy/pallets/compare/v0.4.3...v0.4.4
[0.4.3]: https://github.com/linkyndy/pallets/compare/v0.4.2...v0.4.3
[0.4.2]: https://github.com/linkyndy/pallets/compare/v0.4.1...v0.4.2
[0.4.1]: https://github.com/linkyndy/pallets/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/linkyndy/pallets/compare/v0.3.1...v0.4.0
[0.3.1]: https://github.com/linkyndy/pallets/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/linkyndy/pallets/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/linkyndy/pallets/compare/v0.1.0...v0.2.0
