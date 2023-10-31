[![Black](https://github.com/Rainyan/action-sp-cvar-docs/actions/workflows/black.yml/badge.svg)](.github/workflows/black.yml)
[![MyPy](https://github.com/Rainyan/action-sp-cvar-docs/actions/workflows/mypy.yml/badge.svg)](.github/workflows/mypy.yml)

# action-sp-cvar-docs
Automatic Markdown documentation for SourceMod plugin ConVars.

## Example
Create the file `.github/workflows/docs.yml` at the root of the repo:
```yml
name: Update cvar docs

# Controls when the workflow will run
on:
  # Triggers the workflow on push or pull request events but only for the main branch
  push:
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
        uses: Rainyan/action-sp-cvar-docs@v1
        with:
          dry_run: false
```
