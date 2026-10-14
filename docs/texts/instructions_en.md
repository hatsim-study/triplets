# Task Instructions

<!-- Version instructions_en v1.1, 14 Oct 2026 (sentence on near-static control scenes added).The question wording in Section 2 is the preregistered English wording (preregistration v1.1, Section 2 / Section 12) and must not be changed. The key bindings in Section 3 must match the implementation in web/; if the application changes, update this text and its version. Drop Section 5 (practice triplets) if the application has no practice phase. -->

## 1. What you will see

The screen shows three short videos playing in a loop:

- **at the top**, one reference video,
- **at the bottom left and bottom right**, two candidates.

All three videos play simultaneously and repeat until you answer. They have no sound.

## 1a. Two studies, the same task

On the introductory screen you choose between the **grass study** (40 trials, about 6–8 minutes; all clips show grass and shrubs — the differences in motion, e.g. wind and the rhythm of swaying, and in the structure of the vegetation are subtle, judge them as carefully as pronounced differences), the **mixed scenes study** ({{N_TRIALS}} trials, about {{DURATION}}; water, foliage, smoke, flags, machinery and other dynamic textures) and **both** (the two parts one after the other in random order; after the first part you can continue right away or finish the second part another day). The question and the controls are the same in both parts.

## 2. The question

In every trial you answer the same question:

> **Which of the two lower clips is more similar to the upper one in its overall dynamic visual character?**

Possible answers: **left**, **right**, **cannot decide**.

### What "overall dynamic visual character" means

The overall impression of how the video looks **and** how it moves — taken together: speed and rhythm of motion, its regularity or restlessness, surface structure and graininess, colour, contrast. Judge the clip as a whole, not a single detail.

**It is not about content.** We are not asking whether the videos show the same kind of thing (two waters, two grasses). Two videos of entirely different things can have a very similar character, and two videos of the same thing can differ markedly in character. For example, if the left clip is water and the right clip is grass, but the grass sways in the same way as the reference wheat field, the grass may be more similar — or the water may be, if its motion and appearance match the reference better. Your overall impression decides.

### The answer "cannot decide"

This is a legitimate answer and is not penalised in any way. Use it when both candidates genuinely appear equally similar, or equally dissimilar, to the reference and you cannot lean towards either. If you lean towards one side even slightly, choose that side. "Cannot decide" is not meant for trials that merely feel difficult — difficult trials are fine; answer by impression.

## 3. Controls

| Answer | Key | On-screen button |
|---|---|---|
| the left clip is more similar | **left arrow** (←) | "Left" |
| the right clip is more similar | **right arrow** (→) | "Right" |
| cannot decide | **down arrow** (↓) | "Cannot decide" |

The answer is recorded immediately on key press or click and the next triplet appears. Answers cannot be undone — if you make a mistake, just continue; an isolated slip does not affect the result. You do not need to use the mouse or keyboard while watching.

Recommendation: let the videos run through at least once (a few seconds) and then answer according to your first overall impression. There is no need to analyse the videos at length; a typical trial takes 5–20 seconds. Answers given less than about one second after the triplet appears cannot be regarded as a judgement and are flagged by the application.

## 4. Course of the session

- A session has **{{N_TRIALS}} trials**. The counter at the top shows how many remain.
- {{BREAK_SENTENCE}}
- Some triplets are **repeated** during the session, possibly with the sides swapped. This is intentional. Do not try to remember what you answered before; always answer according to your current impression.
- Some clips **hardly move at all**. This is intentional — they are control scenes. Judge them like all the others: by their overall character, including the fact that they hardly move.
- For some triplets the answer will seem **obvious**. These triplets are part of the task too; answer them in the same way as the others.
- Individual trials have no time limit. If you need to stop, close the window; an unfinished session is not counted and you may start a new one (at most two sessions in total).
- Do not resize the window or switch to other applications during the session; the videos might stop. If a video does not play, the application records this — continue with the trial, or skip it with the "Playback problem" button [DEV NOTE: remove this sentence if the button is not implemented].

## 5. Practice triplets

Before the session starts you will see one or two practice triplets. They are only for trying out the controls and are not recorded. During practice, try each of the three answers so that you know where the keys are.

## 6. Summary

1. Watch all three videos.
2. Ask yourself: *Which of the two lower clips is more similar to the upper one in its overall dynamic visual character?*
3. Press ← or →. Press ↓ only when you are genuinely undecided.
4. {{BREAK_SENTENCE}} {{N_TRIALS}} trials in total.
5. After the last trial a thank-you screen with your completion code appears — that is the end of the session; you can close the window.
