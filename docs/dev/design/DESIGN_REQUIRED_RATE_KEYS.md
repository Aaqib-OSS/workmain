# Required Rate Keys for Paid Providers — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261118
**Originating item:** Issue #155

---

## 1. Purpose

Issue #155 asks that a paid provider price requests only at the rates in its `config/ai_settings.json` entry. A provider whose entry lacks a rate key must refuse construction instead of falling back to a rate written into its code. The issue also asks that `workmain providers test` report why an enabled provider failed construction. This study measures the current state of both and sets out the two design choices the spec depends on: how a missing rate key surfaces through `ProviderManager`, and where the check is written.

## 2. Scope of the read

Read, at `origin/main` 87491bf:

- `workmain/ai/providers/claude.py`, `workmain/ai/providers/gemini.py`: constructors, `estimate_cost`, `validate_config`.
- `workmain/ai/base_provider.py`: `BaseProvider.__init__`, `REQUIRED_POLICY_KEYS`, the error hierarchy.
- `workmain/ai/provider_manager.py`: `get_provider`, `is_disabled`, `generate`, `estimate_cost`, `_load_config`, `_load_provider_policy`, `_require_positive_int`.
- `workmain/cli/commands/providers.py` `test_provider`.
- `docs/AI_SETTINGS_GUIDE.md`, all of it.
- `config/ai_settings.json` `providers`.
- Every tracked file outside `docs/archive/` that names `cost_per_1k`, or one of the four built-in rate literals.
- The full test suite, run with a probe plugin kept outside the repository, which logged every `ClaudeProvider` and `GeminiProvider` construction whose config lacked a rate key.

Not read: `workmain/ai/providers/ollama.py` beyond its constructor calls in tests, because the issue puts Ollama out of scope. Files under `scripts/baseline/` match the census search. #188 restricts them, and this study neither reads nor cites them.

## 3. Findings

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F1 | Both paid providers read each rate with a built-in fallback. Claude's are `0.003` / `0.015`, Gemini's `0.00015` / `0.0006`. The issue cites lines 66-67 and 69-70. The lines have since moved. | `workmain/ai/providers/claude.py:71-72`, `workmain/ai/providers/gemini.py:72-73`, `__init__`: `config.get('cost_per_1k_prompt_tokens', <rate>)` | High |
| F2 | The rates price both the recorded cost of every reply and every pre-generation estimate. `generate()` sets `cost = self.estimate_cost(...)`. `ProviderManager.estimate_cost` calls the provider's `estimate_cost`, and `ReportGenerator` reports it as `estimated_cost`. | `claude.py:144`, `gemini.py:163`, `provider_manager.py:384`, `report_generator.py:266` | — |
| F3 | Both enabled paid providers carry both keys in the live config, so the built-in rates are not in use today. | `config/ai_settings.json:13-14` (claude), `:29-30` (gemini) | — |
| F4 | The guide no longer carries rate values. Commit ac083c4 (20261009) removed the stale Gemini rates that the issue cites. § Gemini-Specific Fields now reads "Same fields as Claude." The guide does not say the keys are required, or that rates are never fetched from the vendor. § Common Fields says "every `cost_per_1k_*` field [is] set by Ray". | `docs/AI_SETTINGS_GUIDE.md:48`, `:54-55`, `:61-63` | Medium |
| F5 | The guide's § How to add a new provider, step 4, shows a config section for a new provider with no rate keys. A paid provider added from it would fail construction once rates are required. | `docs/AI_SETTINGS_GUIDE.md:205-214` | Medium |
| F6 | **The `providers test` misreport described in the issue is already fixed.** Commit 978d538 (#225, closed 20261015, after #155 was opened on 20261001) records a construction failure only in `_disabled_reasons`. `is_disabled` is then False, `get_provider` raises with the reason, and `test_provider` prints it to stderr and exits 3. Existing tests cover both halves of the issue's fourth criterion. One shows the construction error and no disabled message for an enabled provider with its API key unset. The other shows the enable instruction for a provider with `enabled: false`. | `provider_manager.py:111-112`, `:132-140`, `:153-155`, `:468-477`; `providers.py:145-154`, `:201-208`; `tests/test_provider_foundation.py::TestFailedConstruction::test_providers_test_reports_construction_error`, `::test_providers_test_config_disabled_exits_0` | — |
| F7 | `ProviderManager` handles a missing required config value in two ways. **Fatal at load:** a call type's `max_tokens` (`_parse_call_config` → `_require_positive_int`) and the payload policy file (`_load_provider_policy`, deliberately run before construction "so an unusable policy raises out of here rather than being recorded as a construction failure") both raise out of `_load_config`, and no command can build the manager. **Per-provider construction failure:** any exception from a provider's constructor is caught and recorded in `_disabled_reasons`. That covers a missing API key and a missing `model` (each provider's `validate_config`). The provider is unavailable, and every other provider works. | `provider_manager.py:410-427`, `:466-477`, `:532-534`, `:607-618`; `claude.py:238-242`, `gemini.py:276-280` | — |
| F8 | `ConfigurationError` and `ProviderUnavailableError` are both `ProviderError`. `ProviderManager.generate` catches `ProviderError` from the primary provider. With `fallback_mode: auto`, the fallback provider answers and the returned `FallbackNotice` carries the reason. All five call types in the live config use `auto`. `ReportGenerator` stores the reason as the report's `fallback_reason`, and condensation from `notes` prints it. Whether every other entry path shows the notice was not traced. | `base_provider.py:260`, `:272`; `provider_manager.py:280-311`; `config/ai_settings.json:56`, `:65`, `:74`, `:83`, `:94`; `report_generator.py:188`, `:208`; `cli/commands/notes.py:670-671` | — |
| F9 | `BaseProvider` already has a declared-key mechanism for the payload policy. A subclass sets `REQUIRED_POLICY_KEYS`, `missing_policy_keys()` computes the gap, and `BaseProvider.__init__` refuses construction naming the missing keys. There is no equivalent for `config`. | `base_provider.py:117-125`, `:146-153` | — |
| F10 | Suite baseline: 1787 passed (run 20261118). Thirteen tests build a Claude or Gemini provider from a config with neither rate key. The table below lists them. Each depends on construction getting past the point where a rate check would sit, or on which error it raises first. | Probe run, 20261118 | — |

Tests from F10. Each builds a provider with no rate keys:

- `tests/test_ai_providers_offline.py::TestProviderManagerPolicyLoading::test_valid_policy_constructs_provider`
- `tests/test_provider_foundation.py::TestFailedConstruction::test_providers_list_shows_error_not_disabled`
- `tests/test_provider_foundation.py::TestFailedConstruction::test_providers_test_reports_construction_error`
- `tests/test_provider_foundation.py::TestProviderPolicyContract::test_claude_missing_policy_names_both_keys`
- `tests/test_provider_foundation.py::TestProviderPolicyContract::test_claude_missing_policy_names_only_absent_key`
- `tests/test_provider_foundation.py::TestProviderPolicyContract::test_constructor_uses_missing_policy_keys`
- `tests/test_provider_foundation.py::TestProviderPolicyContract::test_gemini_missing_policy_names_key`
- `tests/test_provider_foundation.py::test_claude_provider_reads_model_from_config`
- `tests/test_provider_foundation.py::test_claude_provider_requires_model_in_config`
- `tests/test_provider_foundation.py::test_gemini_provider_reads_model_from_config`
- `tests/test_provider_foundation.py::test_gemini_provider_requires_model_in_config`
- `tests/test_provider_foundation.py::test_is_disabled_false_when_enabled_but_failed_api_key`
- `tests/test_provider_foundation.py::test_provider_disabled_by_construction_failure_reports_reason`

## 4. Options

### Q1 — How a missing rate key surfaces through `ProviderManager`

#### Option A — Per-provider construction failure

- **Approach:** The provider's constructor raises `ConfigurationError` naming the key. `ProviderManager` records it in `_disabled_reasons`, as it does a missing `model` or API key (F7). No change to `provider_manager.py`.
- **Pros:** Nothing is priced at a wrong rate: the provider does not run. The reason is visible through `providers list` (`error`), `providers test` (F6), `get_provider`, and the fallback reason on reports (F8). A typo in one provider's rate does not stop commands that never use it. That includes the daemon's Ollama intent parsing. A required value in a provider's own config entry is handled the same way as the other required values in that entry (`model`, API key). The application files are `claude.py` and `gemini.py`, so the work stays inside `hotfix/*`.
- **Cons:** With `fallback_mode: auto`, a call type whose primary provider lacks a rate key is answered by its fallback. The operator learns of it from a fallback notice, not from a refusal.

#### Option B — Fatal at manager load

- **Approach:** `ProviderManager._load_config` checks each enabled paid provider's rate keys before construction, as `_load_provider_policy` checks the policy, and raises out of `_load_config`. The constructor still refuses as well, so the issue's first criterion holds for direct construction.
- **Pros:** Matches the wording "the way `ProviderManager` already refuses a missing `max_tokens`". Nothing can run until the config is fixed.
- **Cons:** One provider's typo stops every command and the daemon. The check is written twice, in the manager and in the constructor, or it needs a new declared-key mechanism for `BaseProvider` to share. The policy precedent was fatal for a reason that does not apply here. A policy typo would have *silently* sent the wrong request. A missing rate key under Option A sends nothing and says why. At least `provider_manager.py` joins the file set, plus `base_provider.py` with a shared mechanism. That makes four application files, which escalates to `feature/*` (`docs/standards/2-git.md` §2.2).

**Recommendation: Option A.** The defect is silent mispricing. Option A ends it, and the failure stays visible on every surface that already reports a construction failure. It treats a required key in a provider's config entry the same as that entry's other required keys, so it adds no second path. Option B reaches a stricter outcome by adding a manager-side check that the defect does not need, and it widens the effect of one typo to every command.

### Q2 — Where the check is written

#### Option C — Each paid provider's constructor

- **Approach:** `ClaudeProvider.__init__` and `GeminiProvider.__init__` read each rate key without a default, and raise `ConfigurationError` naming the key when it is absent. The check is written once in each of the two files.
- **Pros:** It is the issue's own direction, and it adds no mechanism the issue did not name. It matches how each provider already refuses a missing `model` (F7).
- **Cons:** The same two-key check is written in two places. A future paid provider must remember to add it. The guide's § How to add a new provider, step 2, would say so.

#### Option D — Declared config keys on `BaseProvider`

- **Approach:** A `REQUIRED_CONFIG_KEYS` class attribute, with a check in `BaseProvider.__init__` that mirrors `REQUIRED_POLICY_KEYS` (F9). Claude and Gemini declare both rate keys, and Ollama declares none.
- **Pros:** One check, and a new paid provider declares its keys instead of writing the check.
- **Cons:** It adds a public class attribute and behaviour to `BaseProvider`, a mechanism the issue did not ask for (`.claude/skills/session-start/references/spanner.md` § Working rules, "Build only what the issue asks for"). It adds `base_provider.py` to the file set, making three application files, which is still `hotfix/*`. Required keys would then live in two places: the declared set, and the `model` / API key checks in `validate_config`.

**Recommendation: Option C.** The issue asks for the refusal, not for a mechanism, and two providers do not justify a new public contract on `BaseProvider`. If a third paid provider is added, a declared-key mechanism can be proposed as its own issue.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | When a paid provider's config entry lacks a rate key, should that provider alone be unavailable (Option A: recorded as a construction failure, other providers and the fallback keep working), or should `ProviderManager` refuse to load so that no command runs (Option B)? | |
| Q2 | Is the check written in each paid provider's constructor (Option C), or declared once on `BaseProvider` as `REQUIRED_CONFIG_KEYS` (Option D)? | |

## 6. Disposition

- Promoted to:
- Superseded by:
