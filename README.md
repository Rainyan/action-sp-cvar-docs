[![Black](https://github.com/Rainyan/action-sp-cvar-docs/actions/workflows/black.yml/badge.svg)](.github/workflows/black.yml)
[![MyPy](https://github.com/Rainyan/action-sp-cvar-docs/actions/workflows/mypy.yml/badge.svg)](.github/workflows/mypy.yml)

# action-sp-cvar-docs
Automatic Markdown documentation for SourceMod plugin ConVars.

This action will scan all your SourcePawn code files (specified by `--code_patterns` regex) for ConVars created by `CreateConVar`, then look for the first Markdown file matching the `--doc_patterns` regex, and from within it, look for the first Markdown header matching the `--header_patterns` regex, and replace that header's contents with the parsed cvar info.

## Usage
To get started, copy the *docs.yml* GitHub action from [the example](#Example).

This action follows [SemVer](https://semver.org/), and offers binding to the latest major version, using:
```yml
uses: Rainyan/action-sp-cvar-docs@vN
```
where `N` is the [latest major tag](https://github.com/Rainyan/action-sp-cvar-docs/tags).

The action will accept all of the optional arguments for the underlying [*document.py*](document.py) script as input parameters. For any multi-word arguments, replace any dashes with underlines for the input parameters.
```
usage: document.py [-h] [-C CODE_PATTERNS] [-D DOC_PATTERNS] [-H HEADER_PATTERNS] [--dry-run] [--encoding ENCODING] [--format-filename FORMAT_FILENAME] [--format-cvarname FORMAT_CVARNAME]
                   [--format-cvarprop FORMAT_CVARPROP]
                   cwd

Automatic Markdown documentation for SourceMod plugin ConVars.

positional arguments:
  cwd                   Current working directory.

options:
  -h, --help            show this help message and exit
  -C CODE_PATTERNS, --code_patterns CODE_PATTERNS
                        RegEx pattern for code files to match.
  -D DOC_PATTERNS, --doc_patterns DOC_PATTERNS
                        RegEx pattern for documentation files to match.
  -H HEADER_PATTERNS, --header_patterns HEADER_PATTERNS
                        RegEx pattern for documentation headers to match for the location of the cvar docs placeholder.
  --dry-run             If set, print the output to stdout instead of writing to file.
  --encoding ENCODING   Encoding to use for file read/write operations.
  --format-filename FORMAT_FILENAME
                        Formatting for the code file name, with placeholder !a!. This is skipped if parsing one single code file.
  --format-cvarname FORMAT_CVARNAME
                        Formatting for the cvar name, with placeholder !a!.
  --format-cvarprop FORMAT_CVARPROP
                        Formatting for the cvar property, with placeholder !a! (property name), and !b! (property default value).
```

For example:
```yml
with:
  dry_run: true
```
would use the `--dry-run` mode, which only prints the change to stdout instead of writing it to file, and:
```yml
with:
  format_cvarname: '* **!a!**\n'
```
would render the cvar name (`!a!`) with **\*\*bold\*\***.

For the input arguments' default values, see the [argument parser code](https://github.com/search?q=repo%3ARainyan%2Faction-sp-cvar-docs+ArgumentParser&type=code).

## Example
### Action file
Using the file `.github/workflows/docs.yml` at the root of the repo:
```yml
name: Update cvar docs

# Controls when the workflow will run
on:
  # Triggers the workflow on pull request events but only for the main branch
  pull_request:
    branches: [ main, master ]
    paths:
      - '.github/workflows/docs.yml'
      - '*.sp'
      - '*.inc'
      - '*.md'
  # Allows you to run this workflow manually from the Actions tab
  workflow_dispatch:

jobs:
  update-docs:
    permissions:
      contents: write
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Update docs
        uses: Rainyan/action-sp-cvar-docs@v3
```

### Plugin file
Assuming there exists an `example.sp` file in the repo:
```sp
#include <sourcemod>

ConVar foo;

public void OnPluginStart()
{
	foo = CreateConVar("foo", "The default value", "This variable adjusts the foo.",
		_, true, 0.0, true, float(MaxClients));
}
```

### Readme file
And there exists a `README.md` file at the root of the repo:
```md
# Test
Lorem ipsum.
## Usage
<!-- A header at any level will work, as long as it matches the --header_patterns regex -->
### Cvars
This line will be replaced.
This line will also be replaced.
### But the following header will persist.
As will the text after it.
```

#### Results:
The action will update the `README.md` file:
```md
# Test
Lorem ipsum.
## Usage
<!-- A header at any level will work, as long as it matches the --header_patterns regex -->
### Cvars
* foo
  * Default value: `The default value`
  * Description: `This variable adjusts the foo.`
  * Min: `0.0`
  * Max: `float(MaxClients)`
### But the following header will persist.
As will the text after it.
```
## Contribution
PRs are most welcome! I'm mostly using this for my personal projects, but am publishing it here in case someone else also finds it useful.
If you have any ideas on how to improve this tool, please do consider submitting a patch.
