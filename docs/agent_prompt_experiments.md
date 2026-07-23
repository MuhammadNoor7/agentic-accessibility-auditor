# Agent Prompt Experiments — Week 4
**Status:** FINAL (as of Week 7 — re-tested blockers, no change)
**Author:** Ayesha Naveed
**Date:** July 2026
**Goal:** Compare the 4 configured LLM providers (Anthropic, OpenAI, Gemini, Groq) for the explainer agent, to resolve TBD-01.

## Method

Ran `scripts/run_explainer_sample.py --count 3 --max-violations-per-screen 5` against each provider — 3 sample screens, 5 violations each (15 total), using the existing `src/explainer.py` prompt template. No prompt changes were made; this round tests provider quality, not prompt variants.

## Results by provider

### Groq (llama-3.3-70b-versatile) — ✅ Tested, working

Groq successfully explained all 15 of 15 violations. The full run completed in well under a minute, and since it's on the free tier, no billing was required.

The tone throughout was clear, professional, and consistent. Explanations correctly matched the actual violation — missing labels and duplicate labels were correctly identified with the right resource IDs — and the suggested fixes were concrete, real code (e.g. `android:contentDescription="Chat"`) rather than vague advice. No hallucination was observed; explanations stayed grounded in the violation data provided, with no invented details.

The one weakness: explanations for the same rule (e.g. R01) were fairly template-like across different screens, with low variation in phrasing.

### Gemini (gemini-2.0-flash) — ⚠️ Blocked

The initial attempt failed with `API_KEY_INVALID`. The root cause was that the repo's `google-generativeai` package is deprecated and doesn't support Google's newer API key format (keys starting `AQ.Ab...` instead of `AIza...`). Noor fixed this by switching the dependency to `google-genai` (requirements.txt + `src/llm_providers.py` updated).

After that fix, authentication succeeded but hit a second blocker: `429 RESOURCE_EXHAUSTED`, quota limit `0` on the free tier — a known, widely-reported issue in 2026 where Google requires a billing account linked (with a $0 spend cap) to unlock free-tier quota.

**Status:** Not tested end-to-end. Would need billing linked to retry.

### Anthropic (claude-opus-4-8) — ⚠️ Blocked

No free tier is available — a minimum $5 prepaid credit is required to generate an API key.

**Status:** Not tested. Awaiting team decision on shared budget.

### OpenAI (gpt-4o) — ⚠️ Blocked

No free credits are available as of 2026 — paid billing is required to generate an API key.

**Status:** Not tested. Awaiting team decision on shared budget.

## Summary comparison

Of the four providers, only Groq could actually be tested, and it performed well: clear, accurate explanations with specific, code-level fixes, delivered fast and at no cost.

Gemini was free to test in principle but was blocked by a quota bug requiring a linked billing account, so no quality assessment could be made. Anthropic and OpenAI were both blocked outright — Anthropic requires a $5 minimum prepaid credit, and OpenAI has no free tier at all — so neither could be evaluated either.

## Recommendation

See `docs/TBD-01-decision.md` for the formal resolution.

## Sample output
# Explainer sample review

## chat_1054

### R01 / c_040 (High)
- **Input issue:** Missing accessible label
- **Guideline IDs:** G01, G02, G30
- **Explanation:** The AppCompatImageView component with the resource id com.pinkapp:id/jumpToTop has an empty text and content description, which makes it inaccessible to screen readers. This means that users who rely on screen readers will not be able to identify the purpose or function of this component.
- **User impact:** Blind and low vision users will be affected as they will not be able to navigate or interact with this component using their screen readers. This can lead to frustration and difficulty in using the app.
- **Fix:** Add a content description to the component, for example, android:contentDescription="Jump to top"

### R02 / c_040 (High)
- **Input issue:** Image button without description
- **Guideline IDs:** G02, G30
- **Explanation:** The AppCompatImageView component with the resource id com.pinkapp:id/jumpToTop is an image button but it does not have a content description, which is required for blind users to understand its purpose or function.
- **User impact:** Blind users will be affected as they will not be able to understand the purpose or function of this image button using their screen readers.
- **Fix:** Add a content description to the component, for example, android:contentDescription="Jump to top"

### R03 / c_052 (Medium)
- **Input issue:** Duplicate labels
- **Guideline IDs:** G03
- **Explanation:** The AppCompatButton component with the resource id com.pinkapp:id/unlockButton1 has the text 'Play zapping' which is duplicated elsewhere in the app, which can cause confusion for screen reader users who rely on unique text or content descriptions to navigate.
- **User impact:** Blind and cognitive users will be affected as they may get confused between identical buttons with the same text or content description, leading to incorrect interactions.
- **Fix:** Change the text of one of the buttons to a unique value, for example, 'Play now' or add a unique content description.

### R03 / c_054 (Medium)
- **Input issue:** Duplicate labels
- **Guideline IDs:** G03
- **Explanation:** The AppCompatButton component with the resource id com.pinkapp:id/unlockButton2 has the text 'Later' which is duplicated elsewhere in the app, which can cause confusion for screen reader users who rely on unique text or content descriptions to navigate.
- **User impact:** Blind and cognitive users will be affected as they may get confused between identical buttons with the same text or content description, leading to incorrect interactions.
- **Fix:** Change the text of one of the buttons to a unique value, for example, 'Remind me later' or add a unique content description.

### R03 / c_033 (Medium)
- **Input issue:** Duplicate labels
- **Guideline IDs:** G03
- **Explanation:** The AppCompatButton component with the resource id com.pinkapp:id/unlockButton2 has the text 'Later' which is duplicated elsewhere in the app, which can cause confusion for screen reader users who rely on unique text or content descriptions to navigate.
- **User impact:** Blind and cognitive users will be affected as they may get confused between identical buttons with the same text or content description, leading to incorrect interactions.
- **Fix:** Change the text of one of the buttons to a unique value, for example, 'Remind me later' or add a unique content description.

## chat_10560

### R01 / c_015 (High)
- **Input issue:** Missing accessible label
- **Guideline IDs:** G01, G02, G30
- **Explanation:** The MessageCenterListView has an empty text and content description, making it inaccessible to screen readers. This component has a class of com.apptentive.android.sdk.module.messagecenter.view.MessageCenterListView and a resource id of com.bongocomics.futuramaland:id/message_list.
- **User impact:** Blind and low vision users will not be able to identify the purpose of this interactive element. This will cause confusion and make it difficult for them to navigate the app.
- **Fix:** Set a content description for the MessageCenterListView, e.g., android:contentDescription="Message list"

### R01 / c_034 (High)
- **Input issue:** Missing accessible label
- **Guideline IDs:** G01, G02, G30
- **Explanation:** The AppCompatEditText has an empty text and content description, making it inaccessible to screen readers. This component has a class of android.support.v7.widget.AppCompatEditText and a resource id of com.bongocomics.futuramaland:id/composing_et.
- **User impact:** Blind and low vision users will not be able to identify the purpose of this interactive element. This will cause confusion and make it difficult for them to navigate the app.
- **Fix:** Set a content description for the AppCompatEditText, e.g., android:contentDescription="Message composition field"

### R01 / c_035 (High)
- **Input issue:** Missing accessible label
- **Guideline IDs:** G01, G02, G30
- **Explanation:** The ApptentiveImageGridView has an empty text and content description, making it inaccessible to screen readers. This component has a class of com.apptentive.android.sdk.util.image.ApptentiveImageGridView and a resource id of com.bongocomics.futuramaland:id/grid.
- **User impact:** Blind and low vision users will not be able to identify the purpose of this interactive element. This will cause confusion and make it difficult for them to navigate the app.
- **Fix:** Set a content description for the ApptentiveImageGridView, e.g., android:contentDescription="Image grid"

### R01 / c_036 (High)
- **Input issue:** Missing accessible label
- **Guideline IDs:** G01, G02, G30
- **Explanation:** The FloatingActionButton has an empty text and content description, making it inaccessible to screen readers. This component has a class of android.support.design.widget.FloatingActionButton and a resource id of com.bongocomics.futuramaland:id/composing_fab.
- **User impact:** Blind and low vision users will not be able to identify the purpose of this interactive element. This will cause confusion and make it difficult for them to navigate the app.
- **Fix:** Set a content description for the FloatingActionButton, e.g., android:contentDescription="Compose message"

### R05 / c_034 (High)
- **Input issue:** Unlabeled input field
- **Guideline IDs:** G05, G20
- **Explanation:** The AppCompatEditText has an empty hint, text, and content description, making it inaccessible to screen readers. This component has a class of android.support.v7.widget.AppCompatEditText and a resource id of com.bongocomics.futuramaland:id/composing_et.
- **User impact:** Blind and cognitive users will not be able to identify the purpose of this input field. This will cause confusion and make it difficult for them to navigate the app.
- **Fix:** Set a hint for the AppCompatEditText, e.g., android:hint="Type your message"

## chat_11382

### R01 / c_029 (High)
- **Input issue:** Missing accessible label
- **Guideline IDs:** G01, G02, G30
- **Explanation:** The CircleButtonView with resource id 'com.mixlr.android:id/chatButton' has an empty text and content description, which means that screen readers will not be able to announce its purpose to blind or low vision users. Since it's an interactive element, it needs a visible or programmatic label.
- **User impact:** Blind or low vision users will not be able to understand the purpose of this button, and may accidentally trigger it or be unable to trigger it at all, due to lack of accessible information.
- **Fix:** Set a content description for the CircleButtonView, for example: android:contentDescription="Chat"

### R01 / c_032 (High)
- **Input issue:** Missing accessible label
- **Guideline IDs:** G01, G02, G30
- **Explanation:** The ImageButton with resource id 'com.mixlr.android:id/goLiveButton' has an empty text and content description, which means that screen readers will not be able to announce its purpose to blind or low vision users. Since it's an interactive element, it needs a visible or programmatic label.
- **User impact:** Blind or low vision users will not be able to understand the purpose of this button, and may accidentally trigger it or be unable to trigger it at all, due to lack of accessible information.
- **Fix:** Set a content description for the ImageButton, for example: android:contentDescription="Go Live"

### R01 / c_033 (High)
- **Input issue:** Missing accessible label
- **Guideline IDs:** G01, G02, G30
- **Explanation:** The PlayButtonView with resource id 'com.mixlr.android:id/volume_mute_button' has an empty text and content description, which means that screen readers will not be able to announce its purpose to blind or low vision users. Since it's an interactive element, it needs a visible or programmatic label.
- **User impact:** Blind or low vision users will not be able to understand the purpose of this button, and may accidentally trigger it or be unable to trigger it at all, due to lack of accessible information.
- **Fix:** Set a content description for the PlayButtonView, for example: android:contentDescription="Mute Volume"

### R01 / c_040 (High)
- **Input issue:** Missing accessible label
- **Guideline IDs:** G01, G02, G30
- **Explanation:** The RelativeLayout has an empty text and content description, which means that screen readers will not be able to announce its purpose to blind or low vision users. Since it's an interactive element, it needs a visible or programmatic label.
- **User impact:** Blind or low vision users will not be able to understand the purpose of this element, and may accidentally trigger it or be unable to trigger it at all, due to lack of accessible information.
- **Fix:** Set a content description for the RelativeLayout, or replace it with a more specific widget that can provide a visible label, for example: android:contentDescription="Navigation Header"

### R01 / c_042 (High)
- **Input issue:** Missing accessible label
- **Guideline IDs:** G01, G02, G30
- **Explanation:** The ToggleButton with resource id 'com.mixlr.android:id/bioSwitch' has an empty text and content description, which means that screen readers will not be able to announce its purpose to blind or low vision users. Since it's an interactive element, it needs a visible or programmatic label.
- **User impact:** Blind or low vision users will not be able to understand the purpose of this toggle button, and may accidentally trigger it or be unable to trigger it at all, due to lack of accessible information.
- **Fix:** Set a content description for the ToggleButton, for example: android:contentDescription="Bio Switch"

## chat_11389

### R01 / c_029 (High)
- **Input issue:** Missing accessible label
- **Guideline IDs:** G01, G02, G30
- **Explanation:** The CircleButtonView with resource id 'com.mixlr.android:id/chatButton' has no text and no content description, making it inaccessible to screen readers. This button's action cannot be understood by users who rely on assistive technologies.
- **User impact:** Blind and low vision users will not be able to understand the purpose or action of this button, making it difficult or impossible for them to use it. This affects users who rely on screen readers to navigate the app.
- **Fix:** Add a content description to the CircleButtonView, for example: android:contentDescription="Chat"

### R01 / c_032 (High)
- **Input issue:** Missing accessible label
- **Guideline IDs:** G01, G02, G30
- **Explanation:** The ImageButton with resource id 'com.mixlr.android:id/goLiveButton' has no text and no content description, making it inaccessible to screen readers. The button's small bounds also suggest it may be difficult to tap for users with motor impairments.
- **User impact:** Blind users will not be able to understand the purpose or action of this button, making it difficult or impossible for them to use it. This affects users who rely on screen readers to navigate the app.
- **Fix:** Add a content description to the ImageButton, for example: android:contentDescription="Go Live"

### R01 / c_033 (High)
- **Input issue:** Missing accessible label
- **Guideline IDs:** G01, G02, G30
- **Explanation:** The PlayButtonView with resource id 'com.mixlr.android:id/volume_mute_button' has no text and no content description, making it inaccessible to screen readers. Although the button is currently not enabled, it still requires an accessible label.
- **User impact:** Blind and low literacy users will not be able to understand the purpose or action of this button when it is enabled, making it difficult or impossible for them to use it. This affects users who rely on screen readers to navigate the app.
- **Fix:** Add a content description to the PlayButtonView, for example: android:contentDescription="Mute Volume"

### R01 / c_040 (High)
- **Input issue:** Missing accessible label
- **Guideline IDs:** G01, G02, G30
- **Explanation:** The RelativeLayout has no text and no content description, and although it is clickable, its purpose or action cannot be understood by screen readers.
- **User impact:** Blind and low vision users will not be able to understand the purpose or action of this clickable region, making it difficult or impossible for them to use it. This affects users who rely on screen readers to navigate the app.
- **Fix:** Add a content description to the RelativeLayout, for example: android:contentDescription="Main Menu". Additionally, consider using a more semantic element, such as a Button, to improve accessibility.

### R01 / c_042 (High)
- **Input issue:** Missing accessible label
- **Guideline IDs:** G01, G02, G30
- **Explanation:** The ToggleButton with resource id 'com.mixlr.android:id/bioSwitch' has no text and no content description, making it inaccessible to screen readers. This button's state (on or off) and purpose cannot be understood by users who rely on assistive technologies.
- **User impact:** Blind users will not be able to understand the purpose or action of this button, making it difficult or impossible for them to use it. This affects users who rely on screen readers to navigate the app.
- **Fix:** Add a content description to the ToggleButton, for example: android:contentDescription="Bio Switch"

## chat_11390

### R01 / c_029 (High)
- **Input issue:** Missing accessible label
- **Guideline IDs:** G01, G02, G30
- **Explanation:** The CircleButtonView with resource_id 'com.mixlr.android:id/chatButton' has an empty text and content description, which means that screen readers will not be able to provide any information about this button to blind or low vision users. As a circle button view, it's likely that this button has an icon or image, but without a content description, the purpose of the button is unclear to users relying on screen readers.
- **User impact:** Blind or low vision users will not be able to understand the purpose of this button, as their screen readers will not provide any information about it. This will make it difficult or impossible for them to use this button.
- **Fix:** Add a content description to this button, for example: android:contentDescription="@string/chat_button_description" where chat_button_description is a string resource describing the action of the button, such as 'Open chat'.

### R01 / c_032 (High)
- **Input issue:** Missing accessible label
- **Guideline IDs:** G01, G02, G30
- **Explanation:** The ImageButton with resource_id 'com.mixlr.android:id/goLiveButton' has an empty text and content description. Since it's an image button, it likely has an image or icon, but without a content description, screen readers will not be able to inform users about the button's purpose.
- **User impact:** Blind users will not be able to understand the purpose of this button, as their screen readers will not provide any information about it. This will make it difficult or impossible for them to use this button.
- **Fix:** Add a content description to this button, for example: android:contentDescription="@string/go_live_button_description" where go_live_button_description is a string resource describing the action of the button, such as 'Go live'.

### R01 / c_033 (High)
- **Input issue:** Missing accessible label
- **Guideline IDs:** G01, G02, G30
- **Explanation:** The PlayButtonView with resource_id 'com.mixlr.android:id/volume_mute_button' has an empty text and content description. As a play button view, it likely has an icon or image, but without a content description, the purpose of the button is unclear to users relying on screen readers.
- **User impact:** Blind or low literacy users will not be able to understand the purpose of this button, as their screen readers will not provide any information about it. This will make it difficult or impossible for them to use this button.
- **Fix:** Add a content description to this button, for example: android:contentDescription="@string/volume_mute_button_description" where volume_mute_button_description is a string resource describing the action of the button, such as 'Mute volume'.

### R01 / c_040 (High)
- **Input issue:** Missing accessible label
- **Guideline IDs:** G01, G02, G30
- **Explanation:** The RelativeLayout is clickable but has an empty text and content description. As it does not have a clear purpose or label, screen readers will not be able to provide any information about this view to users.
- **User impact:** Blind or low vision users will not be able to understand the purpose of this view, as their screen readers will not provide any information about it. This will make it difficult or impossible for them to use this view.
- **Fix:** Add a content description to this view, for example: android:contentDescription="@string/relative_layout_description" where relative_layout_description is a string resource describing the action or purpose of the view.

### R01 / c_042 (High)
- **Input issue:** Missing accessible label
- **Guideline IDs:** G01, G02, G30
- **Explanation:** The ToggleButton with resource_id 'com.mixlr.android:id/bioSwitch' has an empty text and content description. As a toggle button, it likely has a purpose or action associated with it, but without a content description, screen readers will not be able to inform users about the button's purpose.
- **User impact:** Blind users will not be able to understand the purpose of this button, as their screen readers will not provide any information about it. This will make it difficult or impossible for them to use this button.
- **Fix:** Add a content description to this button, for example: android:contentDescription="@string/bio_switch_description" where bio_switch_description is a string resource describing the action of the button, such as 'Toggle bio visibility'.

## Finalization note (Week 7)

As of Week 7, Anthropic and OpenAI still require paid billing (no free tier), and Gemini remains blocked by Google's free-tier quota bug — confirmed unchanged since original testing. This doc is being finalized with Groq as the sole tested and recommended provider. If team budget or Google's quota issue changes in the future, re-run `scripts/run_explainer_sample.py` against the newly-available provider(s) and update this doc with a real comparison at that time.