# Changelog

## [1.3.0](https://github.com/chenwei791129/commit-with-ai/compare/v1.2.0...v1.3.0) (2026-06-16)


### Features

* **providers:** add codex-oauth provider using local codex OAuth token ([fab1ad8](https://github.com/chenwei791129/commit-with-ai/commit/fab1ad8c19b05f6f497df2e36c1247c6e5b1070e))


### Documentation

* **readme:** add Codex OAuth usage instructions ([355af85](https://github.com/chenwei791129/commit-with-ai/commit/355af853e6f87c43cc328d5fb187af3c46a6b5df))

## [1.2.0](https://github.com/chenwei791129/commit-with-ai/compare/v1.1.0...v1.2.0) (2026-03-24)


### Features

* **claude-cli:** use stdin for prompt and add --no-session-persistence flag ([246d1ae](https://github.com/chenwei791129/commit-with-ai/commit/246d1aed64e608b78466dfb562759cb9a1938a9b))


### Documentation

* update claude-cli-provider spec and archive optimize-cli-invocation change ([ca9ea1c](https://github.com/chenwei791129/commit-with-ai/commit/ca9ea1c91f031d61d4df679fa21c676150c963e9))

## [1.1.0](https://github.com/chenwei791129/commit-with-ai/compare/v1.0.1...v1.1.0) (2026-03-23)


### Features

* add Claude CLI provider via subprocess invocation ([c2e22ba](https://github.com/chenwei791129/commit-with-ai/commit/c2e22bab26f364f35fc0a2aca50ef1372c88d911)), closes [#8](https://github.com/chenwei791129/commit-with-ai/issues/8)


### Documentation

* add CLAUDE.md and AGENTS.md project instructions ([75974d7](https://github.com/chenwei791129/commit-with-ai/commit/75974d7c669e4e8f3ecee6f772a84bface972808))
* add PyPI package link to README resources ([449dda2](https://github.com/chenwei791129/commit-with-ai/commit/449dda20d63b3c578d5aed27d3f4de9ca3cee171))
* update README for multi-provider support and archive Spectra change ([226135d](https://github.com/chenwei791129/commit-with-ai/commit/226135d17e8aaa1dc0e6c9e01d3088401168df80))

## [1.0.1](https://github.com/chenwei791129/commit-with-ai/compare/v1.0.0...v1.0.1) (2026-01-30)


### Documentation

* update repository name from git-auto-commit to commit-with-ai ([e8f2150](https://github.com/chenwei791129/commit-with-ai/commit/e8f2150ce3df5d8b240bf0509f0a58b1f8ba2e1f))
* use bash commands for git alias setup ([4a032e8](https://github.com/chenwei791129/commit-with-ai/commit/4a032e8b0d0ac79a0313d7fb306b84b93931d29e))

## [1.0.0](https://github.com/chenwei791129/git-auto-commit/compare/v0.1.0...v1.0.0) (2026-01-30)


### ⚠ BREAKING CHANGES

* Package renamed from git-auto-commit to commit-with-ai due to PyPI naming conflict.

### Features

* rebrand as commit-with-ai ([1c84cc8](https://github.com/chenwei791129/git-auto-commit/commit/1c84cc8637da0f54098ff9a1998628f47a6a0e3d))

## 0.1.0 (2026-01-30)


### Features

* **cli:** enable single-character selection for menu choices ([7f3042e](https://github.com/chenwei791129/git-auto-commit/commit/7f3042e1f93ce8ee03b8f66fefa3c7b26fa666ca))
* initial release of git-auto-commit ([135e3d9](https://github.com/chenwei791129/git-auto-commit/commit/135e3d938e4503afdb345d75e92371e34fb2cf62))
* prepare for PyPI publication ([ba0bfcf](https://github.com/chenwei791129/git-auto-commit/commit/ba0bfcf71f80cf8548237f6ff41458a86cb1b6c6))


### Bug Fixes

* **ci:** explicitly fetch tags before checking for release ([03163b2](https://github.com/chenwei791129/git-auto-commit/commit/03163b2d4a3d1e8520168cb520271597b25bc33b))
* **ci:** fetch tags in publish workflow ([fe6593b](https://github.com/chenwei791129/git-auto-commit/commit/fe6593b7c6136f5f897e53b52531a9a23ad40ec7))
* **ci:** remove uv cache config (no uv.lock file) ([23b886f](https://github.com/chenwei791129/git-auto-commit/commit/23b886fe1b25f3022cfad9aeeef0ce9e279f8bcd))
* **ci:** simplify release-please config to use v-prefixed tags ([32b0407](https://github.com/chenwei791129/git-auto-commit/commit/32b040782ef30dd58f67c5fab378f9d98fb21ec3))
* **ci:** use workflow_run trigger for PyPI publish ([ea4aa96](https://github.com/chenwei791129/git-auto-commit/commit/ea4aa96947783073251f22bd08506c0c3336594a))
* **cli:** enable arrow keys and editing in input prompts ([69f6c9e](https://github.com/chenwei791129/git-auto-commit/commit/69f6c9e1ad4d5abe6600324a0a44797d3c611867))
* **compat:** support python 3.10 and above ([6b0fdaf](https://github.com/chenwei791129/git-auto-commit/commit/6b0fdaf3c59b4d53d13f60797fb99dc9446a4fca))


### Documentation

* remove install dependencies section from README ([18b69b9](https://github.com/chenwei791129/git-auto-commit/commit/18b69b911059bb0ee68eded13601b3ae82946ba1))
* simplify usage section to git alias only ([51207d7](https://github.com/chenwei791129/git-auto-commit/commit/51207d740c6682227a6b3328f6f674f0ab747788))

## [0.2.0](https://github.com/chenwei791129/git-auto-commit/compare/git-auto-commit-v0.1.0...git-auto-commit-v0.2.0) (2026-01-30)


### Features

* **cli:** enable single-character selection for menu choices ([7f3042e](https://github.com/chenwei791129/git-auto-commit/commit/7f3042e1f93ce8ee03b8f66fefa3c7b26fa666ca))
* initial release of git-auto-commit ([135e3d9](https://github.com/chenwei791129/git-auto-commit/commit/135e3d938e4503afdb345d75e92371e34fb2cf62))
* prepare for PyPI publication ([ba0bfcf](https://github.com/chenwei791129/git-auto-commit/commit/ba0bfcf71f80cf8548237f6ff41458a86cb1b6c6))


### Bug Fixes

* **cli:** enable arrow keys and editing in input prompts ([69f6c9e](https://github.com/chenwei791129/git-auto-commit/commit/69f6c9e1ad4d5abe6600324a0a44797d3c611867))
* **compat:** support python 3.10 and above ([6b0fdaf](https://github.com/chenwei791129/git-auto-commit/commit/6b0fdaf3c59b4d53d13f60797fb99dc9446a4fca))


### Documentation

* remove install dependencies section from README ([18b69b9](https://github.com/chenwei791129/git-auto-commit/commit/18b69b911059bb0ee68eded13601b3ae82946ba1))
* simplify usage section to git alias only ([51207d7](https://github.com/chenwei791129/git-auto-commit/commit/51207d740c6682227a6b3328f6f674f0ab747788))
