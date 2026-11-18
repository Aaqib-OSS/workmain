# Paid Providers Require Their Rate Keys — Implementation Results

**Status:** Shipped
**Author:** Anvil (Role 3)
**Date:** 20261118
**Spec:** `../specs/REQUIRED_RATE_KEYS_SPEC.md`
**Released as:** v1.60.0 (tag v1.60.0)

---

## 1. Summary

Complete. `BaseProvider` declares `REQUIRED_CONFIG_KEYS` and `missing_config_keys()`, and refuses construction when a declared key is absent, before the policy check and before any vendor client exists. `ClaudeProvider` and `GeminiProvider` declare both rate keys and read them with no fallback, so no rate value remains in provider code. `ProviderManager._load_config` refuses an enabled provider whose entry lacks a declared key, naming `providers.<name>.<key>`, before the policy load and outside the construction `try/except`. A disabled provider is not checked. `docs/AI_SETTINGS_GUIDE.md` states that rates are required, set by hand and never fetched.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | DR1–DR6: the config contract on `BaseProvider`, the rate key declarations and fallback removal in both paid providers, the load-time refusal in `ProviderManager`, and rate keys in the fixtures of the 18 tests the spec's §2 lists. Commit f6667a2. | `workmain/ai/base_provider.py`, `workmain/ai/providers/claude.py`, `workmain/ai/providers/gemini.py`, `workmain/ai/provider_manager.py`, `tests/test_provider_foundation.py`, `tests/test_ai_providers_offline.py` | +14 |
| 2 | The guide's § Common Fields, § Claude-Specific Fields and § How to add a new provider steps 2 and 4. Commit fb5a0b2. | `docs/AI_SETTINGS_GUIDE.md` | +0 |
| 3 | This artifact. | `docs/dev/results/REQUIRED_RATE_KEYS_RESULTS.md` | +0 |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | `pytest tests/test_provider_foundation.py::TestProviderConfigContract -k direct_construction_without_rate_key`: 4 passed. Each case asserts the missing key is named and the patched vendor client was not called. |
| AC1.2 | Met | `pytest tests/test_provider_foundation.py::TestProviderConfigContract -k manager_load_without_rate_key`: 4 passed. Each case asserts `providers.<name>.<key>` in the raised `ConfigurationError` and the vendor client not called. |
| AC1.3 | Met | `pytest tests/test_provider_foundation.py::TestProviderConfigContract -k disabled_provider_without_rate_keys`: 2 passed. |
| AC1.4 | Met | `pytest tests/test_provider_foundation.py::TestProviderConfigContract -k "constructor_uses_missing_config_keys or manager_load_uses_missing_config_keys"`: 2 passed. |
| AC1.5 | Met | `pytest tests/test_provider_foundation.py::TestProviderConfigContract -k estimate_cost_uses_configured_rates`: 2 passed, with rates 0.0021 / 0.0137. |
| AC1.6 | Met | `pytest` on the 18 node IDs the spec's §2 lists: 18 passed. `git diff dev -- tests/test_provider_foundation.py tests/test_ai_providers_offline.py`: every removed line is a fixture line that gains rate keys; no assertion is removed or changed. See §5 for the four policy tests. |
| AC2.1 | Met | `/usr/bin/grep -rn "get(\s*['\"]cost_per_1k_\|0\.00015\|0\.0006\|0\.003\|0\.015" workmain/ai/providers/`: zero hits, exit 1. Before Step 1 it returned the four lines `claude.py:71-72`, `gemini.py:72-73`. AC1.1 shows a missing key reaches no fallback. |
| AC3.1 | Met | Ray, 20261118: Reviewed the `docs/AI_SETTINGS_GUIDE.md` for § Common Fields, § Claude-Specific Fields and § How to add a new provider steps 2 and 4: would someone adding or editing a paid provider know the rates are required, where they go and that nothing fetches them. |
| AC4.1 | Met | `pytest tests/test_provider_foundation.py::TestFailedConstruction::test_providers_test_reports_construction_error tests/test_provider_foundation.py::TestFailedConstruction::test_providers_test_config_disabled_exits_0`: 2 passed. |
| AC5.1 | Met | Bare `pytest`: 1801 passed, 0 failed, 0 skipped (1787 + 14). |

## 4. Deviations and decisions

| # | Departure or ambiguity | Step stopped at | Resolution | Resolved by |
| --- | --- | --- | --- | --- |

None.

**Decisions below the contract.**

| # | Step | Decision | Considered instead | Why |
| --- | --- | --- | --- | --- |
| 1 | 1 | One module constant `_TEST_RATES` (0.0021 / 0.0137) in `tests/test_provider_foundation.py` serves the DR6 fixtures there and test (vi). `tests/test_ai_providers_offline.py` writes the same two values inline in `_temp_ai_settings`. | Separate values for the fixtures and for test (vi); importing the constant across test files. | The values are invented and unlike every built-in rate, so one constant meets both DR6 and DR7. A cross-file import would couple two test modules for two numbers. |
| 2 | 1 | Tests (i), (ii), (iii) and (vi) are parametrized over a `_PAID_PROVIDERS` table (class, entry name, API key variable, env, vendor client patch path, policy), and (i) and (ii) also over the two rate keys. | One test function per provider and key. | The cases differ only in data; the case IDs (`claude-cost_per_1k_prompt_tokens`, …) name each one. |
| 3 | 1 | For the four tests built through `_failed_construction_manager`, the rate keys are added in that helper to the entry it enables, not in `_make_temp_settings`. | Adding rate keys to `_make_temp_settings`. | `_make_temp_settings` keeps Claude and Gemini disabled and is used by many tests that need no rates; test (iii) relies on it carrying none. The change stays on the fixture of the listed tests. |
| 4 | 1 | Test (ii) shows "before the provider is constructed" by asserting the patched vendor client was never called, alongside the raise naming `providers.<name>.<key>`. | Patching the provider's `__init__`. | A refusal from the constructor would be caught by `_load_config`'s `except Exception` and recorded, so the raise itself already shows the manager path; the client assertion adds that nothing was built. |
| 5 | 1 | Test (iii) asserts the entry is `enabled: false` and holds no rate key before loading. | Relying on the helper's contents unchecked. | The test cannot then pass on a fixture that later gains rate keys. |
| 6 | 1 | Messages: `BaseProvider` raises `<Class> config is missing required key(s): <keys>`, mirroring its policy message; `ProviderManager` raises `config/ai_settings.json is missing required key(s): providers.<name>.<key>, …`. | Naming the class in the manager message. | DR2 lets each caller write its own message; the manager's names the file and the dotted path the spec requires. |
| 7 | 1 | Removed "Previously accepted ProviderConfig dataclass — changed in v1.1 Provider Foundation Sprint." from the `BaseProvider.__init__` docstring, and moved the `_load_config` docstring summary to its second line and gave it a `Raises:` section. | Leaving both as they were. | `automation/style_check.py` flagged the history citation and D213 on the docstrings Step 1 edits; a style violation is fixed before the commit. |
| 8 | 1 | The `Raises:` sections of `ClaudeProvider.__init__` and `GeminiProvider.__init__` are unchanged. | Adding the config refusal to them. | The step names the `BaseProvider` and `_load_config` docstrings. The refusal is raised by `BaseProvider.__init__`, whose docstring states it, as the policy refusal already was. |
| 9 | 2 | The new sentences are appended to the "Cost values are Ray's" paragraph itself. | A separate paragraph after it. | Step 2(a) names that paragraph. |
| 10 | 2 | Step 4's example writes the rate placeholders as quoted strings (`"<USD per 1,000 prompt tokens>"`). | Bare placeholders. | The example's other placeholders are quoted, and a bare placeholder would make the block invalid JSON. |

## 5. Verification

- **Test suite:** 1801 passed, 0 failed, 0 skipped (baseline: 1787 passed, 0 failed, 0 skipped) — form per `docs/standards/6-testing.md` §6.
- **Defect shown before the fix:** tests (i) and (ii), `TestProviderConfigContract::test_direct_construction_without_rate_key_raises` and `::test_manager_load_without_rate_key_raises`, each over `claude`/`gemini` × both rate keys.
  - Step 1(a), before DR1–DR5: 8 failed, each with `Failed: DID NOT RAISE <class 'workmain.ai.base_provider.ConfigurationError'>`.
  - Step 1(d), after: 8 passed (with (iii)–(vi), 14 passed).
- **Existing tests before the fixture change:** after DR1–DR5 and before Step 1(c), the suite was 14 failed, 1781 passed. The 14 were the spec's 18 less the four `TestProviderManagerPolicyLoading` tests that assert a bare `ConfigurationError` (`test_policy_error_absent_file`, `_unparseable`, `_missing_required_key`, `_does_not_land_in_disabled`), which passed on the rate refusal, as the spec's §2 and §7 predicted. After the fixture change, running that class's `_run` with each fake loader raises the policy error itself: `payload policy file is missing`, `is not valid JSON`, and `is missing required key(s): thinking`.
- **Checks:** `automation/architecture_check.py`: 0 new findings, PASS. `automation/style_check.py`: 0 violations, PASS.
- **Live verification:** at close-out, 20261118, on this branch: `workmain providers list` against the live `config/ai_settings.json` exited 0. `ProviderManager` loaded under the new rate key check, and Claude, Gemini and Ollama all show `available`. The live config carries both rate keys on both enabled paid providers (the spec's §2). The close-out preflight suite: 1801 passed, 0 failed, 0 skipped.
- **Daemon restart:** close-out's (`docs/standards/2-git.md` §2.6).

## 6. Follow-ups

| Item | Description | Why deferred |
| --- | --- | --- |
| Issue #155 body | The second acceptance criterion's check becomes the spec's AC2.1 command, `grep -rn …` (the spec's Decision Log). | Edited at close-out (`docs/standards/1-workflow.md` §1.2). |
| #295 | Other values providers read with a fallback written in code, and the missing `model` handled as a construction failure. | Out of scope (the spec's Decision Log, Q4). |
