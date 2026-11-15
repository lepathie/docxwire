# Spec Delta

## MODIFIED Requirements

### Requirement: The command takes a single document path
The `docxwire` command SHALL accept exactly one positional argument: the path
to a `.docx` file, and SHALL additionally accept the optional flags `--json`
(machine-readable output) and `--settings-env` (load settings from
environment variables). A missing argument, an unknown option, or a missing
or unreadable file, SHALL be reported as an actionable error and SHALL exit
non-zero without contacting the site.

#### Scenario: A single document path is accepted
- **WHEN** the command is invoked with one existing `.docx` path
- **THEN** the run proceeds with that document

#### Scenario: A missing argument is a usage error
- **WHEN** the command is invoked without a document path
- **THEN** a usage error is reported and the command exits non-zero

#### Scenario: A missing file is reported
- **WHEN** the command is invoked with a path that does not exist
- **THEN** an actionable error naming the file is reported and the command
  exits non-zero without contacting the site

#### Scenario: An unknown option is a usage error
- **WHEN** the command is invoked with an option it does not support
- **THEN** a usage error is reported and the command exits non-zero without
  contacting the site

### Requirement: Settings are loaded from the current working directory
The command SHALL by default load its settings from the `settings.toml` file
in the current working directory, and SHALL, when invoked with
`--settings-env`, load them from the `DOCXWIRE_JOOMLA_*` environment
variables instead, using exactly one source per run. A missing or invalid
settings source SHALL be reported with an actionable message and SHALL exit
non-zero before any conversion or network activity.

#### Scenario: The settings file in the working directory is used
- **WHEN** a `settings.toml` exists in the current working directory and the
  command is invoked with a valid document
- **THEN** the run uses that file's Joomla settings

#### Scenario: A missing settings file is reported
- **WHEN** no `settings.toml` exists in the current working directory
- **THEN** an actionable error pointing to the example settings file is
  reported and the command exits non-zero without contacting the site

#### Scenario: The environment source is used with --settings-env
- **WHEN** the command is invoked with `--settings-env` and the
  `DOCXWIRE_JOOMLA_*` environment variables are set
- **THEN** the run uses the environment variables' Joomla settings without
  requiring a `settings.toml` in the working directory

#### Scenario: A missing environment source is reported
- **WHEN** the command is invoked with `--settings-env` and a required
  `DOCXWIRE_JOOMLA_*` variable is missing
- **THEN** an actionable message naming the variable is reported and the
  command exits non-zero without contacting the site

### Requirement: A successful run reports the created article
On success the command SHALL report the created article's id and the
article's review note — the `Prüfe: …` line when items need review, and an
indication that nothing needs review when the note is empty — and SHALL exit
0. When invoked with `--json`, the command SHALL instead write a single JSON
object to stdout: on success carrying the created article's `id`, its
`title`, and the note (empty string when nothing needs review), and on an
operational failure carrying the error message as `error` — with the same
exit codes (0 success, non-zero failure) as the default output.

#### Scenario: The id and note are reported
- **WHEN** a run creates an article whose note is `Prüfe: Titel`
- **THEN** the output carries the created article's id and the note line and
  the command exits 0

#### Scenario: A clean article is reported as clean
- **WHEN** a run creates an article with an empty note
- **THEN** the output carries the created article's id and indicates that
  nothing needs review, and the command exits 0

#### Scenario: A successful run with --json reports a JSON object
- **WHEN** a run with `--json` creates an article
- **THEN** stdout is a single JSON object carrying the created article's
  `id`, `title`, and `note`, and the command exits 0

#### Scenario: A failed run with --json reports a JSON object
- **WHEN** a run with `--json` fails (for example an image upload API error)
- **THEN** stdout is a single JSON object carrying the error message as
  `error`, and the command exits non-zero
