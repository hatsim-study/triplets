# Ethics Review Application — Summary (English)

**Document version:** ethics_application_en v1.0, 10 Oct 2026 (abridged English version of `ethics_application_cs.md`; the Czech document is the one submitted)
**Status:** no confirmatory vote will be collected before a favourable opinion of the committee.

## 1. Title

Perceived similarity of dynamic visual materials: an online triplet study for the validation of a computational video-similarity measure (working name: HAT-SIM triplet study).

## 2. Investigators

Principal investigator: [TO BE COMPLETED BY AUTHORS]. Department: [TO BE COMPLETED BY AUTHORS: faculty and department, Czech Technical University in Prague]. Funding: [TO BE COMPLETED BY AUTHORS]. Intended output: a peer-reviewed computer-vision paper (CVPR 2027 submission) and a public anonymous dataset.

## 3. Aim

To test whether a fixed, non-learned similarity descriptor for dynamic textures predicts the majority human choice in a triplet task at least as well as the strongest learned baseline, and to measure the human agreement ceiling against which any such measure must be read. Human judgements serve only as reference data for evaluating algorithms; nothing about the participants themselves is under study. Hypothesis and analysis plan are preregistered (Section 11).

## 4. Design

- Online, anonymous, two-alternative forced choice with a "cannot decide" option. Triplet: reference clip on top, two candidates below. Question: "Which of the two lower clips is more similar to the upper one in its overall dynamic visual character?"
- Session: 60 trials, 12–15 minutes, break after 30 trials; at most 2 sessions per participant; ≥ 75 participants, ≈ 200 sessions, ≈ 11,800 trials before exclusions.
- Randomisation of candidate side, triplet order and loop phase. In-session quality control: 10 % mirrored repeats, 5 % attention triplets with an obvious answer (one candidate identical to the reference).
- Each triplet collects ≥ 5 decided votes from distinct observers (max 7); a subset is re-judged by a second independent panel to estimate the human ceiling.
- Pilot: ≤ 10 observers on stimuli outside the main study; never merged with the main analysis; same consent and rules.
- Web application in the participant's browser; desktop computer with window ≥ 900 px required; mobile devices refused.

## 5. Stimuli

DynTex, a public academic database of dynamic textures (Péteri, Fazekas & Huiskes, Pattern Recognition Letters 2010), licensed for research use [TO BE COMPLETED BY AUTHORS: confirm licence terms]. Natural scenes and materials (water, vegetation, fire, smoke, fabrics, flags, regular surfaces, distant traffic). No clip shows a person close up; **a few clips contain distant figures or vehicles** without recognisable faces or number plates. No violent, sexual or otherwise sensitive content. Presentation: H.264 mp4, 352 × 288 px, 10 s loops, silent; no flicker or flashes; some clips contain fast natural motion; in a secondary family some clips are shown at 1.5× or 2× playback speed. The stimulus manifest (SHA-256), triplet list and seeds are frozen before data collection and will be published.

## 6. Recruitment, eligibility

Channels: [TO BE COMPLETED BY AUTHORS: course e-mails, student channels, departmental channels, personal networks]. Recruitment texts attached; they do not state the expected outcome or the algorithms compared. Compensation: [TO BE COMPLETED BY AUTHORS: none / course credit as one of several equivalent options; instructors see only self-submitted completion codes]. Eligibility: age ≥ 18 (self-declared by ticking the consent box); normal or corrected vision; computer with current browser and stable connection. Self-exclusion advised for photosensitive epilepsy or discomfort with fast-moving images.

## 7. Risks and their mitigation

No risk beyond ordinary video viewing. Mild eye or mental fatigue: 60-trial cap, mid-session break, no per-trial time limit, free withdrawal, at most two sessions. Photosensitivity: stimuli contain no flicker; explicit warning in consent, recruitment and information sheet. Content: natural scenes only, all stimuli annotated before collection. No performance feedback; participants are told there are no right answers. No deception: the purpose is disclosed in advance; only the specific algorithms and expected result are withheld, which the debriefing explains. Repeated and attention triplets are announced neutrally in the instructions.

## 8. Data and GDPR

Recorded: per trial — session id, pseudonymous observer id, trial index, triplet and clip identifiers, side, response, response time, loop phases, repeat/attention flags, playback-error count, UTC timestamp, interface language, screen size; per session — observer's session number (1/2), consent version and time, age band, vision correction (yes/no), language, start/end time, trials completed, user-agent string, completion code.
Not recorded: name, e-mail, IP address (not logged by the server [TO BE COMPLETED BY AUTHORS: confirm web-server/proxy/hosting configuration]), exact age, gender, location, third-party cookies, tracking code.
Pseudonymisation: observer id is a random string generated in the browser and kept in local storage, used only to prevent repeated triplets and to enforce the two-session limit; the completion code is random and is the sole means by which a participant can designate records for deletion.
Legal basis: [TO BE COMPLETED BY AUTHORS: Art. 6(1)(a) consent / Art. 6(1)(e) scientific research in the public interest; consult the DPO]. Controller: [TO BE COMPLETED BY AUTHORS: CTU in Prague, faculty]; DPO: [TO BE COMPLETED BY AUTHORS]. No special-category data [TO BE COMPLETED BY AUTHORS: confirm with DPO that "vision correction yes/no" is acceptable, or drop the item].
Storage: EU-located server [TO BE COMPLETED BY AUTHORS], HTTPS, access restricted to investigators; raw pseudonymous data retained for [TO BE COMPLETED BY AUTHORS: e.g. 10 years].
Withdrawal: until [TO BE COMPLETED BY AUTHORS: close of data collection] via completion code; afterwards user agent and completion codes are removed, data are merged and become anonymous; deletion is then no longer possible, as stated in the consent and debriefing.
Publication: anonymous triplet- and session-level dataset (votes, response times, age band, vision correction, language, screen size; no user agent, no completion codes, timestamps coarsened to day [TO BE COMPLETED BY AUTHORS: confirm]) in an open repository [TO BE COMPLETED BY AUTHORS: Zenodo/OSF/institutional], together with the stimulus manifest (hashes; not the videos, subject to the DynTex licence).

## 9. Preregistered exclusion rules

Applied after collection and before any metric is computed (two-stage unlocking); independent of any personal attribute; all counts reported. Observer excluded (all votes): > 1 failed attention triplet; consistency on repeats < 0.6 with ≥ 5 repeats; median response time < 1.5 s or > 60 s; > 40 % "cannot decide"; incomplete session (< 80 % of trials). Trial excluded: response time < 1 s; logged playback error. Triplet excluded from the primary endpoint: > 50 % "cannot decide" (reported as undecidable). Excluded participants are not notified and any compensation is unaffected.

## 10. Informed consent

Electronic, before the first trial; text attached (`consent_en.md`, `consent_cs.md`) with a longer information sheet; six tick-box statements including age ≥ 18; consent version and timestamp stored per session.

## 11. Preregistration

*Preregistration of the HAT-SIM v9 triplet study*, version 1.1 (9 Oct 2026) with changelog 1.1 → 1.2 (10 Oct 2026); both attached and to be published with SHA-256 hashes [TO BE COMPLETED BY AUTHORS: OSF registration link after the committee's opinion]. Fixes the single confirmatory hypothesis, primary endpoint and test, sample size (≥ 600 test triplets, ≥ 5 votes per triplet, ≥ 75 observers), stimulus construction, majority and ceiling definitions, the exclusion rules above, and the rule that the document does not change after collection starts.

## 12. Timeline

Submission to the committee [TO BE COMPLETED BY AUTHORS]; pilot after the opinion; main data collection [TO BE COMPLETED BY AUTHORS: from–to]; withdrawal deadline = end of collection; analysis and writing [TO BE COMPLETED BY AUTHORS]; data release with the publication.

## 13. Attachments

Consent (CS/EN), information sheet (CS/EN), instructions (CS/EN), recruitment texts (CS/EN), debriefing (CS/EN), preregistration v1.1 + changelog v1.2, [TO BE COMPLETED BY AUTHORS: application screenshots, sample stimulus frames, DPO statement if required].
