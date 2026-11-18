# Paid Providers Require Their Rate Keys — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20261118
**Branch:** `feature/issue-155-required-rate-keys` (from `dev`)
**Target release:** v1.60.0
**Originating item:** Issue #155
**Design study:** `../design/DESIGN_REQUIRED_RATE_KEYS.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261118 | Ray | Study Q1: when an enabled paid provider's entry in `config/ai_settings.json` lacks a rate key, `ProviderManager` refuses to load (study Option B). | Taken — DR4. Rationale is the study's §4 Q1. |
| 20261118 | Ray | Study Q2: each provider class declares the config keys it requires in the provider contract on `BaseProvider`, mirroring `REQUIRED_POLICY_KEYS` (study Option D). | Taken — DR1, DR2, DR3. |
| 20261118 | Ray | Study Q3: the load-time check runs for enabled providers only. | Taken — DR4. |
| 20261118 | Ray | Study Q4: the missing `model` handled as a construction failure (study F12) and the other values written in provider code (study F13) go to one issue. | Out of scope here. Carried to #295, which #155 blocks. |
| 20261118 | Ray | Branch: re-cut from `hotfix/issue-155-required-rate-keys` to `feature/*` from `dev`, because Q1 and Q2 put the change in four application files and add to the provider contract (`docs/standards/2-git.md` §2.2). | Done. The three design-study commits were cherry-picked, and the local `hotfix/*` branch, which was never pushed, was deleted. |
| 20261118 | Spanner | The issue's fourth criterion (`workmain providers test` reports a construction failure, and tells the user to enable only a provider set `enabled: false`) was delivered by #225 (commit 978d538) after #155 was opened (study F6). | AC4.1 maps it to the two existing tests that check it. No code change. |
| 20261118 | Spanner | The issue's second criterion checks with `grep -nE "cost_per_1k_(prompt\|completion)_tokens'\s*," workmain/ai/providers/`. Under DR1 the declared key set in `claude.py` and `gemini.py` matches that pattern. The search also misses a default written with double quotes. It cannot produce the answer its criterion states (`docs/standards/1-workflow.md` §1.2). | AC2.1 restates the check. The issue body's second criterion needs the same edit at close-out. |
| 20261118 | Caliper | 1 and 7, spec defect, non-blocking: AC2.1's check `grep -n "get(\s*['\"]cost_per_1k_\|0\.00015\|0\.0006\|0\.003\|0\.015" workmain/ai/providers/` has no `-r`. With standard GNU grep it prints `grep: workmain/ai/providers/: Is a directory`, exits 2 and shows zero hits both before and after Step 1. Run at 1525d15 with `/usr/bin/grep`: `Is a directory`, exit 2. The four lines the spec says appear "before Step 1" only show up in this session's shell, where `grep` is a function that calls ugrep, and ugrep searches directories recursively. Anywhere else, the check reads no files, so it cannot give the answer its criterion states (`docs/standards/1-workflow.md` §1.2). The issue's second criterion, which Decision Log row 7 says gets the same edit at close-out, also has no `-r`. | **Accepted.** AC2.1 is now `grep -rn ...`, run with GNU grep. `/usr/bin/grep -rn` returns the four lines at 1525d15 (Spanner, 20261118). The close-out edit to the issue body uses the same command. |
| 20261118 | Caliper | 8 and 3, spec defect, non-blocking: the spec contradicts itself on which new tests run before the fix and what they show. Step 1(a) says to run all the new tests and that the tests of AC1.1, AC1.2 and AC1.4 fail. §6 says tests (iii), (v) and (vi) "need DR1, DR2 or DR4 to exist and are run only after". Tests (iv) and (v) both patch `missing_config_keys` with `patch.object`. That method does not exist before DR2, so both stop with `AttributeError` before any assertion runs. Test (iv) therefore shows no defect, and nothing distinguishes it from (v). Tests (iii) and (vi) do not need DR1, DR2 or DR4: with today's code, a disabled provider with no rate keys loads (`provider_manager.py:462-464`), and `estimate_cost` prices at the configured rates (`claude.py:224-226`, `gemini.py:262-264`), so both pass before the fix. The implementer has to guess what to run and record in Step 1(a), and the results artifact's "before" runs depend on that guess. | **Accepted.** Step 1(a) writes and runs only (i) and (ii), the tests that show the defect. Step 1(d) writes (iii)–(vi) after the fix. §6 states the same, with the reason each of (iii)–(vi) shows no defect. |
| 20261118 | Caliper | 3, spec defect, non-blocking: it is unclear whether DR7 covers existing tests. DR7 says "A test of pricing uses rates unlike any built-in rate DR5 removes". §2 lists existing pricing tests that use those exact rates: `_offline_claude_config` (0.003 / 0.015), `_offline_gemini_config` (0.00015 / 0.0006), and the expectations at `tests/test_ai_providers_offline.py:664` and `:685`. Neither §1 nor Step 1 says to change them, and DR6 says only the 18 listed tests' fixtures change. The implementer has to guess whether DR7 means changing those two shared fixtures, which many other offline tests use, or applies only to new test (vi). | **Accepted.** DR7 covers only test (vi). The existing fixtures and expectations are not changed: once DR5 removes the built-in rates, the values they use can come only from their own config. §2's fixture lines are corrected to 369-379. |
| 20261118 | Caliper | Pass at 1525d15, full: 36 items checked, 0 blocking, 3 non-blocking. | n/a |

---

## 1. Scope

**In scope:**

- `workmain/ai/base_provider.py` — the provider contract gains declared required config keys (DR1–DR3).
- `workmain/ai/providers/claude.py`, `workmain/ai/providers/gemini.py` — declare both rate keys, and read them with no fallback value (DR5).
- `workmain/ai/provider_manager.py` — refuses at load an enabled provider whose entry lacks a declared key (DR4).
- `tests/test_provider_foundation.py`, `tests/test_ai_providers_offline.py` — new tests of the contract, and rate keys added to the fixtures of the 18 existing tests §2 lists (DR6).
- `docs/AI_SETTINGS_GUIDE.md` — states that rate keys are required, set by hand and never fetched from the vendor. Its § How to add a new provider gains the declaration and the keys.

**Out of scope:**

- `workmain/ai/providers/ollama.py`. Ollama has no rates, and its `estimate_cost` returns 0 by design (issue #155). It declares no required config keys and is not edited.
- Every other value a provider reads from its config entry with a fallback written in code, and the missing `model` that `validate_config` rejects: #295 (Decision Log, Q4).
- The type or range of a rate value. The issue asks that a missing key be refused. A key present with a non-numeric value is a different defect, and nothing in this spec checks it.
- `workmain/cli/commands/providers.py`. The issue's fourth criterion is already met (Decision Log).
- `config/ai_settings.json`. Both enabled paid providers already carry both keys (§2).
- Tests that read the live `config/ai_settings.json`, such as `_make_gemini_config` and `_load_ai_settings` in `tests/test_ai_providers_offline.py`, are unchanged. The live file carries both keys, so their rate `.get` fallbacks are never used.

## 2. Verified current state

Verified 20261118 at `dev` df06370. That commit is identical to `main` 87491bf in `workmain/`, `tests/`, `config/`, `docs/AI_SETTINGS_GUIDE.md`, `docs/ARCHITECTURE.md` and `docs/standards/`, so every line the design study cites holds here.

| Claim | Evidence |
| --- | --- |
| `ClaudeProvider.__init__` calls `super().__init__(config, policy)` first, then reads `self._cost_per_1k_prompt = config.get('cost_per_1k_prompt_tokens', 0.003)` and `self._cost_per_1k_completion = config.get('cost_per_1k_completion_tokens', 0.015)`, then reads the API key and builds `Anthropic(...)`. | `workmain/ai/providers/claude.py:55-84` |
| `GeminiProvider.__init__` has the same shape with `0.00015` / `0.0006`, then builds `genai.Client(...)`. | `workmain/ai/providers/gemini.py:56-88` |
| Both providers price each reply and each estimate through `estimate_cost`, from those two attributes. | `claude.py:144`, `:213-226`; `gemini.py:163`, `:251-264`; `workmain/ai/provider_manager.py:362-384` |
| `BaseProvider` declares `REQUIRED_POLICY_KEYS: set = set()` and the classmethod `missing_policy_keys(cls, policy) -> list[str]` returning `sorted(cls.REQUIRED_POLICY_KEYS - set(policy))`. `__init__` sets `self.config`, then `self.policy`, then raises `ConfigurationError(f"{type(self).__name__} payload policy is missing required key(s): ...")` when keys are missing. The class docstring says "Each provider reads its own required fields via config.get()". | `workmain/ai/base_provider.py:100-155` |
| `OllamaProvider.__init__(self, config, policy=None)` calls `super().__init__(config, policy)` and declares neither `REQUIRED_POLICY_KEYS` nor any rate key. | `workmain/ai/providers/ollama.py:21-31` |
| `ProviderManager._load_config` stores `self._all_configs[name] = provider_cfg`. A provider with `enabled: false` is added to `_disabled` and skipped with `continue`. `_load_provider_policy(name, cls)` runs next, outside the `try`. Then `cls(provider_cfg, policy)` runs inside `try/except Exception`, which records `_disabled_reasons[name] = str(exc)`. | `workmain/ai/provider_manager.py:455-477` |
| `_load_provider_policy` checks the policy with `cls.missing_policy_keys(...)` and raises `ConfigurationError` naming the file and keys. | `provider_manager.py:386-427` |
| The live config carries both rate keys on `claude` and `gemini`, and none on `ollama`. | `config/ai_settings.json:13-14`, `:29-30`, `:38-50` |
| Provider construction sites, found by `grep -rn "ClaudeProvider(\|GeminiProvider(\|OllamaProvider(\|cls(provider_cfg" --include='*.py' .`, with each hit's call target read. Application: `workmain/ai/provider_manager.py:470` only. Tests: `tests/test_provider_foundation.py` (184, 194, 205, 215, 229, 238, 249, 256, 264, and Ollama at 120-159), `tests/test_ai_providers_offline.py` (112, 200, 278, 407), `tests/test_intent_parser.py:167`, `tests/test_ollama_provider.py:26`. `scripts/` and `automation/` construct no provider directly. `scripts/compare_providers.py` and `tests/mocks/stub_providers.py` go through `ProviderManager`. Classes are also reached by name through `PROVIDER_REGISTRY` (`workmain/ai/providers/__init__.py`), whose one constructing caller is `provider_manager.py:470`. | search output, 20261118 |
| `BaseProvider` subclasses in tests: `MockProvider` (`tests/test_ai_foundation.py:53`), `FailingProvider` and `ReadyProvider` (`tests/test_provider_foundation.py:88`, `:103`). None declares required keys, so DR3 does not reach them. | search output, 20261118 |
| **Existing tests whose fixture builds an enabled Claude or Gemini config with no rate keys** (study F10, extended). Two read-only pytest probes, kept outside the repository, found them. One wrapped `ClaudeProvider.__init__` and `GeminiProvider.__init__`; the other wrapped `ProviderManager._load_provider_policy` to catch tests that stop before construction. **Direct construction (8):** in `tests/test_provider_foundation.py`, `test_claude_provider_reads_model_from_config` (177), `test_claude_provider_requires_model_in_config` (189), `test_gemini_provider_reads_model_from_config` (198), `test_gemini_provider_requires_model_in_config` (210), and in `TestProviderPolicyContract` (222) `test_claude_missing_policy_names_both_keys`, `test_claude_missing_policy_names_only_absent_key`, `test_gemini_missing_policy_names_key`, `test_constructor_uses_missing_policy_keys`. **Through `ProviderManager` (10):** in `tests/test_ai_providers_offline.py`, the five tests of `TestProviderManagerPolicyLoading`, through `_temp_ai_settings` (203); in `tests/test_provider_foundation.py`, `TestProviderPolicyContract::test_manager_precheck_uses_missing_policy_keys` (inline settings), `TestFailedConstruction::test_providers_test_reports_construction_error` and `::test_providers_list_shows_error_not_disabled`, and `test_is_disabled_false_when_enabled_but_failed_api_key`, all through `_failed_construction_manager` (423) and `_make_temp_settings` (302), and `test_provider_disabled_by_construction_failure_reports_reason` (879, inline settings). | probe runs, 20261118: 1787 passed, 0 failed, 0 skipped in each |
| Four of the 18 assert a bare `ConfigurationError` from `ProviderManager`: `test_policy_error_absent_file`, `_unparseable`, `_missing_required_key` and `_does_not_land_in_disabled`. Under DR4, without the fixture change, they would pass on the rate refusal instead of the policy fault they test. | `tests/test_ai_providers_offline.py:243-261` |
| The existing cost tests use configured rates equal to the built-in rates DR5 removes: `_offline_claude_config` uses 0.003 / 0.015, and `_offline_gemini_config` uses 0.00015 / 0.0006. While the built-in rates exist, these tests cannot distinguish a configured rate from the built-in one. | `tests/test_ai_providers_offline.py:63-73`, `:369-379`, `:664`, `:685` |
| The `providers test` behaviour in the issue's fourth criterion is checked by `TestFailedConstruction::test_providers_test_reports_construction_error` (exit 3, the construction reason on stderr, no "is disabled") and `::test_providers_test_config_disabled_exits_0` (output says "is disabled" and "enabled: true"). | `tests/test_provider_foundation.py:443-462`; `workmain/cli/commands/providers.py:145-154`, `:201-208` |
| Guide: § Common Fields carries "**Cost values are Ray's.**" (line 48). § Claude-Specific Fields lists the two rate keys (54-55). § Gemini-Specific Fields reads "Same fields as Claude." (63). § How to add a new provider step 2 describes `REQUIRED_POLICY_KEYS` (191), and step 4's example config has no rate keys (205-214). The guide quotes no rate value. | `docs/AI_SETTINGS_GUIDE.md` |
| Suite baseline: 1787 passed, 0 failed, 0 skipped. | `CHANGELOG.md` [1.59.0]; local run 20261118 |

## 3. Design rules

- **DR1 — A provider declares the keys it requires from its `providers.<name>` entry.** `BaseProvider` gains the class attribute `REQUIRED_CONFIG_KEYS: set = set()`. `ClaudeProvider` and `GeminiProvider` each set it to `{'cost_per_1k_prompt_tokens', 'cost_per_1k_completion_tokens'}`. `OllamaProvider` sets nothing. Owner: `workmain/ai/base_provider.py` (the provider contract, `docs/ARCHITECTURE.md` §2), and each declaration lives in the provider's own module.
- **DR2 — The comparison has one home.** `BaseProvider` gains `@classmethod missing_config_keys(cls, config: dict) -> list[str]`, which returns the declared keys absent from `config`, sorted. `BaseProvider.__init__` and `ProviderManager` both call it, and each writes its own message. Owner: `workmain/ai/base_provider.py`.
- **DR3 — A provider cannot be constructed without a declared key.** `BaseProvider.__init__` raises `ConfigurationError` naming the class and each missing key. The check runs before the policy check, so it also runs before any subclass reads its API key or builds a vendor client. The order matches DR4: the config entry is checked before the policy.
- **DR4 — `ProviderManager` refuses to load an enabled provider whose entry lacks a declared key.**
  - In `_load_config`, for each provider not skipped as `enabled: false`, the manager calls `cls.missing_config_keys(provider_cfg)` before `_load_provider_policy` and outside the `try/except` around construction.
  - When keys are missing, it raises `ConfigurationError` out of `_load_config`. The message names `config/ai_settings.json` and each missing key as `providers.<name>.<key>`.
  - The provider never reaches `_disabled_reasons`, and on this path DR3's check never fires.
  - A provider with `enabled: false` is not checked (Decision Log, Q3).
  - Owner: `workmain/ai/provider_manager.py`, the owner of `config/ai_settings.json` (`docs/ARCHITECTURE.md` §2).
- **DR5 — No rate value is written in provider code.** After DR3, `ClaudeProvider` and `GeminiProvider` read each rate as `config['<key>']`, with no fallback value. No rate literal remains anywhere under `workmain/ai/providers/`. `estimate_cost` and the attributes it reads are otherwise unchanged.
- **DR6 — An existing test fails only on what it tests.** Each of the 18 tests §2 lists gets both rate keys in its fixture, with invented values (`CLAUDE.md` § Client Reference). Its assertions are not changed. A shared helper or constant is the implementer's choice.
- **DR7 — A pricing test this spec adds uses rates unlike any built-in rate DR5 removes** (0.003, 0.015, 0.00015, 0.0006). Such a test could otherwise pass on a leftover default. DR7 covers only test (vi). The existing fixtures `_offline_claude_config` and `_offline_gemini_config`, and the expectations at `tests/test_ai_providers_offline.py:664` and `:685`, are not changed. Once DR5 removes the built-in rates, the values those tests use can come only from their own config.

Anything not covered here: stop as `.claude/skills/session-start/SKILL.md` § Role 3 states.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | **Contract, enforcement and tests.** All new tests go in a class `TestProviderConfigContract` in `tests/test_provider_foundation.py`. Patch the vendor clients as `workmain.ai.providers.claude.Anthropic` and `workmain.ai.providers.gemini.genai.Client`, and use the file's fake well-formed keys `_CLAUDE_ENV` / `_GEMINI_ENV` and valid policies. (a) Write tests (i) and (ii), the tests that show the defect. Run them and record the result: each case fails because no `ConfigurationError` is raised. (b) Make DR1–DR5 in `base_provider.py`, `claude.py`, `gemini.py` and `provider_manager.py`. Update the docstrings these edits make untrue: the `BaseProvider` class docstring, the `__init__` docstring and `Raises:`, and the `_load_config` docstring. (c) Add rate keys to the fixtures of the 18 tests §2 lists (DR6). (d) Write tests (iii)–(vi). Run all of `TestProviderConfigContract`, recording that (i) and (ii) now pass, then run the full suite. **Tests:** (i) for each of Claude and Gemini, and each rate key, direct construction with that key removed raises `ConfigurationError` naming it, and the patched vendor client is never called (4 cases); (ii) for each of Claude and Gemini, and each rate key, `ProviderManager` loading a settings file where that provider is enabled and lacks that key raises `ConfigurationError` naming `providers.<name>.<key>`, before the provider is constructed (4 cases); (iii) for each of Claude and Gemini, a settings file where that provider has `enabled: false` and no rate keys loads, and `is_disabled` is True (2 cases); (iv) `BaseProvider.__init__` calls `missing_config_keys`: patched to return `['x']` on `ClaudeProvider` with a complete config, construction raises naming `x` (1); (v) `ProviderManager` calls `missing_config_keys`: patched the same way, loading raises naming `providers.claude.x` (1); (vi) for each of Claude and Gemini, `estimate_cost(1000, 1000)` built with rates unlike any built-in rate (DR7) equals the sum of the two configured rates (2 cases). | `workmain/ai/base_provider.py`, `workmain/ai/providers/claude.py`, `workmain/ai/providers/gemini.py`, `workmain/ai/provider_manager.py`, `tests/test_provider_foundation.py`, `tests/test_ai_providers_offline.py` |
| 2 | **Guide.** `docs/AI_SETTINGS_GUIDE.md`. (a) § Common Fields, the "Cost values are Ray's" paragraph: state that every enabled paid provider requires `cost_per_1k_prompt_tokens` and `cost_per_1k_completion_tokens`, that `ProviderManager` refuses to load when either is missing and names it, that rates are set by hand in the entry, and that WorkmAIn never fetches them from the vendor. (b) § Claude-Specific Fields: mark both rate rows required. (c) § How to add a new provider, step 2: a provider declares in `REQUIRED_CONFIG_KEYS` every key it requires from its entry, and a paid provider declares both rate keys. (d) Step 4: the example config carries both rate keys, with placeholders and no number. The guide quotes no rate value. | `docs/AI_SETTINGS_GUIDE.md` |
| 3 | **Results artifact.** `docs/dev/results/REQUIRED_RATE_KEYS_RESULTS.md`: the before and after runs of Step 1's defect tests, the suite counts in the form `docs/standards/6-testing.md` §6 states, and AC3.1 recorded `Not met` with `Awaiting Ray` (`docs/standards/1-workflow.md` §1.2). | `docs/dev/results/REQUIRED_RATE_KEYS_RESULTS.md` |

Step 1 is one commit. It changes an invariant of every Claude and Gemini construction, so its call sites and the fixtures that depend on it change with it, and the commit leaves the suite green (`docs/standards/1-workflow.md` §1.4).

### Authorization points

None. This spec contains no migration, no deletion of a GitHub object, no merge to `main`, no force-push, and no change to a service's run state beyond close-out's own.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | A Claude or Gemini provider whose config lacks either rate key cannot be constructed directly. The refusal is a `ConfigurationError` that names the missing key, raised before the vendor client exists, so no request can be priced at a rate that is not in config. | `pytest tests/test_provider_foundation.py::TestProviderConfigContract`, tests (i), 4 cases |
| AC1.2 | Through `ProviderManager`, the path every surface uses to obtain a provider, an enabled Claude or Gemini whose `config/ai_settings.json` entry lacks either rate key stops the load with a `ConfigurationError` naming `providers.<name>.<key>`. The provider is not recorded as a construction failure. | `pytest tests/test_provider_foundation.py::TestProviderConfigContract`, tests (ii), 4 cases |
| AC1.3 | A provider with `enabled: false` does not need rate keys. | `pytest tests/test_provider_foundation.py::TestProviderConfigContract`, tests (iii), 2 cases |
| AC1.4 | The required-key comparison has one home, and both the constructor and the manager's load-time check use it. | `pytest tests/test_provider_foundation.py::TestProviderConfigContract`, tests (iv) and (v) |
| AC1.5 | A Claude or Gemini provider prices requests at the rates in its config. | `pytest tests/test_provider_foundation.py::TestProviderConfigContract`, tests (vi), with rates unlike any built-in rate (DR7) |
| AC1.6 | Every existing test that built an enabled Claude or Gemini config without rate keys still checks what it checked before, and fails only on that. | `pytest` on the 18 node IDs §2 lists: 18 passed. `git diff dev -- tests/test_provider_foundation.py tests/test_ai_providers_offline.py` shows each of their changes adds rate keys to a fixture and changes no assertion |
| AC2.1 | No rate value is written into provider code. A rate is read only from config, with no fallback. | `grep -rn "get(\s*['\"]cost_per_1k_\|0\.00015\|0\.0006\|0\.003\|0\.015" workmain/ai/providers/`, run with GNU grep, returning zero hits (it returns the four lines of §2's first two rows before Step 1), together with AC1.1, which shows a missing key reaches no fallback |
| AC3.1 | `docs/AI_SETTINGS_GUIDE.md` states that a paid provider's rates are set by hand in its config entry, are required, and are never fetched from the vendor. It states how a new paid provider declares them, and quotes no rate value. | A stated reading by Ray of § Common Fields, § Claude-Specific Fields and § How to add a new provider steps 2 and 4: would someone adding or editing a paid provider know the rates are required, where they go and that nothing fetches them? |
| AC4.1 | `workmain providers test <provider>` states why an enabled provider that failed construction is unavailable, and tells the user to enable a provider only when its config sets `enabled: false`. This was delivered by #225 (Decision Log). | `pytest tests/test_provider_foundation.py::TestFailedConstruction::test_providers_test_reports_construction_error tests/test_provider_foundation.py::TestFailedConstruction::test_providers_test_config_disabled_exits_0`: 2 passed |
| AC5.1 | The full suite passes, with no net test loss. | Bare `pytest`: at least 1787 + 14 passed, 0 failed, 0 skipped |

## 6. Test plan

- **Baseline before this work:** 1787 passed, 0 failed, 0 skipped (`CHANGELOG.md` [1.59.0]; confirmed by a local run 20261118).
- **Expected after:** 1801 passed, 0 failed, 0 skipped: the baseline plus the 14 cases of Step 1's tests (i)–(vi).
- `tests/test_provider_foundation.py` — `TestProviderConfigContract`, new, 14 cases. The fixtures of 13 existing tests gain rate keys (DR6).
- `tests/test_ai_providers_offline.py` — `_temp_ai_settings` gains rate keys, covering the five `TestProviderManagerPolicyLoading` tests (DR6). No new tests.
- Tests (i) and (ii) show the defect. They are run in Step 1(a), where they fail, and in Step 1(d), where they pass. Tests (iii)–(vi) are written after the fix and show no defect:
  - (iii) and (vi) would also pass on today's code. They guard the decided scope (Q3) and the configured pricing.
  - (iv) and (v) patch `missing_config_keys`, which does not exist until DR2.

## 7. Risks and rollback

- **One typo stops every command.** After Step 1, an enabled paid provider whose entry lacks a rate key stops `ProviderManager` from loading. Every command that builds it then refuses, and so does the daemon, until the key is restored. That is the decided behaviour (Decision Log, Q1), and it matches a missing `max_tokens` or `accepts`. The live config carries both keys on both enabled paid providers (§2), so nothing changes on merge.
- **A policy test passing on the wrong refusal.** If DR6's fixture change misses one of the four policy tests that assert a bare `ConfigurationError`, that test passes on DR4's rate refusal instead of the policy fault. AC1.6 runs the 18 by node ID and reads their diff.
- **Rollback:** each step is one revertible commit. Reverting Step 1 restores today's behaviour exactly, including the built-in rates. Step 2 is documentation only.
