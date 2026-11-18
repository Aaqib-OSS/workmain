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
- `docs/ARCHITECTURE.md` in full; `docs/standards/1-workflow.md`, `docs/standards/3-code.md`.
- Every `config.get(...)` in `workmain/ai/providers/`, and the open issues covering provider config defaults (#114, #125, #152).
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
| F7 | `ProviderManager` reads `config/ai_settings.json` and enforces its authored content at load. A missing or invalid value raises `ConfigurationError` out of `_load_config`, and no command can build the manager. This covers every provider's `accepts` (enabled or not), each call type's `max_tokens` and `instructions`, provider names, and a call type declared in both blocks. The payload policy file, which it also owns, is checked the same way, before construction. The `_load_provider_policy` docstring states why: the failure "must reach the caller rather than being recorded as a construction failure by the blanket except in `_load_config`". Anything a provider's constructor raises is caught and recorded in `_disabled_reasons`, which makes that provider unavailable while the others work. What the constructors raise today is the environment (the API key read from `.env`, the SDK client) and one authored value, `model` (F12). | `provider_manager.py:410-427`, `:455-477`, `:479-500`, `:532-534`, `:580-593`, `:607-618`; `claude.py:74-84`, `:238-242`; `gemini.py:75-88`, `:276-280` | — |
| F8 | `ConfigurationError` and `ProviderUnavailableError` are both `ProviderError`. `ProviderManager.generate` catches `ProviderError` from the primary provider. With `fallback_mode: auto`, the fallback provider answers and the returned `FallbackNotice` carries the reason. All five call types in the live config use `auto`. `ReportGenerator` stores the reason as the report's `fallback_reason`, and condensation from `notes` prints it. Whether every other entry path shows the notice was not traced. | `base_provider.py:260`, `:272`; `provider_manager.py:280-311`; `config/ai_settings.json:56`, `:65`, `:74`, `:83`, `:94`; `report_generator.py:188`, `:208`; `cli/commands/notes.py:670-671` | — |
| F9 | `BaseProvider` already has a declared-key mechanism for the payload policy. A subclass sets `REQUIRED_POLICY_KEYS`, `missing_policy_keys()` computes the gap, and `BaseProvider.__init__` refuses construction naming the missing keys. There is no equivalent for `config`. | `base_provider.py:117-125`, `:146-153` | — |
| F10 | Suite baseline: 1787 passed (run 20261118). Thirteen tests build a Claude or Gemini provider from a config with neither rate key. The table below lists them. Each depends on construction getting past the point where a rate check would sit, or on which error it raises first. | Probe run, 20261118 | — |
| F11 | `docs/ARCHITECTURE.md` §2 names `workmain/ai/provider_manager.py` as the owner of `config/ai_settings.json`. §1 Configuration files says a configuration file is read only by the module that owns it. §2 names `workmain/ai/base_provider.py` as the owner of "the provider contract", and `workmain/ai/providers/<name>.py` as "one AI provider each". Today a provider receives its `providers.<name>` section as a dict from the manager (`provider_manager.py:470`). | `docs/ARCHITECTURE.md` §1, §2 | — |
| F12 | **Outside scope.** A missing `model` is the one authored `ai_settings.json` value that a provider rejects itself, in `validate_config`, so it becomes a construction failure and not a load refusal. | `claude.py:241-242`, `gemini.py:279-280` | Low |
| F13 | **Outside scope.** The rates are not the only authored provider values that a built-in default silently replaces. Claude and Gemini: `retry_attempts` (3), `retry_delay_seconds` (1.0), `api_key_env` (`ANTHROPIC_API_KEY` / `GOOGLE_API_KEY`). Ollama: `host` (`localhost`), `port` (11434), `model` (`mistral`), `timeout` (30). #125 and #152 discuss `retry_attempts`, and #114 and #152 the timeout key, but none of them asks for the default to be removed. No open issue covers `api_key_env` or Ollama's `host`, `port` and `model` defaults. | `claude.py:69-70`, `:74`; `gemini.py:70-71`, `:75`; `ollama.py:28-31` | Medium |

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

The two questions are linked: where the refusal happens decides who must know which keys a provider requires.

### Q1 — Which module refuses a config entry that lacks a rate key

#### Option A — The provider refuses, as a construction failure

- **Approach:** `ClaudeProvider.__init__` and `GeminiProvider.__init__` read each rate key with no default and raise `ConfigurationError` naming it. `ProviderManager` catches the error and records it in `_disabled_reasons`. The provider is unavailable, and the others work.
- **Pros:** No request is priced at a rate that is not in config. A typo in one provider's rates stops only that provider.
- **Cons:**
  - Validity of `config/ai_settings.json` content would be decided outside its owner (F11). The manager's blanket `except` would turn an authoring defect into the same state as a missing API key. That is the conversion `_load_provider_policy` exists to prevent (F7).
  - Every call type in the live config uses `fallback_mode: auto` (F8). A rate typo on a primary provider would move its call type to the fallback. The routing the operator wrote in `report_types` would be overridden by a typo elsewhere in the file. The operator would see it only as a fallback reason.
  - It extends F12's inconsistency instead of following the file's own rule.

#### Option B — `ProviderManager` refuses at load

- **Approach:** When `_load_config` reaches an enabled provider, it checks that provider's config entry for the keys the provider requires, before constructing it. A missing key raises `ConfigurationError` naming `providers.<name>.<key>` out of `_load_config`, as `_load_provider_policy` does for the payload policy. The provider's constructor also refuses, so direct construction cannot bypass the requirement (the issue's first criterion constructs the provider directly).
- **Pros:**
  - The owner of `config/ai_settings.json` decides the validity of its content (F11), as it does for every other authored key in the file (F7).
  - An authoring defect reaches the operator as an error naming the key. It does not become a silent change of provider.
  - It is what the issue's direction names: refused "the way `ProviderManager` already refuses a missing `max_tokens`".
- **Cons:** Until the key is fixed, every command that builds the manager refuses, and so does the daemon. That includes work that never uses the provider. The same is true today of a missing `max_tokens` or `accepts`, or an absent policy file.

**Recommendation: Option B.** `docs/ARCHITECTURE.md` gives the file one owner, and that owner already refuses every other authored defect in it at load. The code states why a config defect must not become a construction failure (F7), and with automatic fallback, Option A's construction failure silently re-routes work (F8). Option A trades a contained failure for a second rule about what a bad `ai_settings.json` does.

### Q2 — Where the requirement "this provider needs these keys" is stated (needed under Option B)

Under Option B the manager must know which keys each provider requires. Ollama has no rates by design (issue #155), so the answer differs by provider.

#### Option C — The manager names them

- **Approach:** `ProviderManager` holds which providers need rate keys.
- **Defeated:** what a provider requires is part of the provider contract, owned by `workmain/ai/base_provider.py` and stated by each provider (F11). Putting it in the manager gives one fact a second home (`docs/ARCHITECTURE.md` §1, One fact, one home). The next paid provider would need an edit in a module that does not own it.

#### Option D — Each provider class declares its required config keys in the provider contract

- **Approach:** `BaseProvider` gains a class attribute naming required `providers.<name>` keys, with a classmethod that returns the missing ones. This mirrors `REQUIRED_POLICY_KEYS` and `missing_policy_keys` (F9). `ClaudeProvider` and `GeminiProvider` declare both rate keys, and `OllamaProvider` declares none. `ProviderManager._load_config` calls the classmethod before construction, as `_load_provider_policy` does. `BaseProvider.__init__` refuses direct construction with a missing key, as it does for the policy.
- **Pros:** Each fact stays with its owner: the provider says what it requires, the contract defines how that is said, and the file's owner enforces it. It extends an existing owner and an existing pattern instead of adding a parallel path (`docs/ARCHITECTURE.md`, opening paragraph). A future paid provider states its rate keys where it states its policy keys.
- **Cons:** It adds a public attribute and classmethod to the provider contract. The issue does not name that mechanism, so Ray decides it.

**Recommendation: Option D.** It is the only option that keeps the requirement with the provider and the enforcement with the file's owner. Option C is set aside under `docs/ARCHITECTURE.md`'s ownership rule, not as a preference.

### Q3 — Enabled providers only, or every provider (under Option B)

- **Enabled only.** The manager checks an entry only when it constructs the provider. This matches the payload policy check, which runs only for enabled providers (F7). A disabled provider prices nothing: `ProviderManager.estimate_cost` goes through `get_provider`, which refuses a disabled provider (`provider_manager.py:136-140`, `:383`).
- **Every provider.** This matches `accepts`. But `accepts` is checked for every provider because routing eligibility reads it whether or not the provider is enabled (`eligible_provider_names`, `provider_manager.py:642-661`). Nothing reads a disabled provider's rates.

**Recommendation: enabled only.** The reason `accepts` is checked for every provider does not apply to rates.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | When a paid provider's entry in `config/ai_settings.json` lacks a rate key, does `ProviderManager` refuse to load (Option B), or does that provider alone fail construction (Option A)? | Ray, 20261118: Option B. |
| Q2 | Under Option B, does each provider class declare its required config keys in the provider contract on `BaseProvider`, mirroring `REQUIRED_POLICY_KEYS` (Option D)? | Ray, 20261118: Option D. |
| Q3 | Under Option B, is the check run for enabled providers only, or for every provider? | Ray, 20261118: enabled providers only. |
| Q4 | F12 and F13 are outside this issue. Should each become an issue of its own, join #155, or be dropped? | Ray, 20261118: one issue covering F12 and F13 — #295. |

## 6. Disposition

- Promoted to: `../specs/REQUIRED_RATE_KEYS_SPEC.md`; F12 and F13 to issue #295
- Superseded by:
