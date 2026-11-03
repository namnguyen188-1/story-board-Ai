# Minimal additive patch for the *existing* skill
Append the rules below near the scene-generation section of the original `SKILL.md`.
Do not delete any other original functionality and do not replace the existing 9-field schema.

## Cinematic performance realism — REQUIRED
In every scene with living characters, plan one motivated action and 1-2 causally relevant micro-reactions: attention/eyeline, breath, body-weight shift, face, prop contact, and response to others. Specify trigger → intent → physical action → short aftereffect in `TIMED ACTION`; make `END STATE` anatomically and spatially continuous into the next `SETTING & START STATE`. In `AUDIO`, specify speaker, real emotional subtext and timings; non-speakers do not lip-sync. Use natural camera blocking without compulsory zooms, pans or standing-at-camera lines. In `CONSTRAINTS`, prohibit frozen mannequin poses, rubber movement, phantom props, dead eye contact, morphing identities and inaccurate lip sync. Stillness is allowed when narratively motivated (or when the subject is an inanimate statue), not as accidental absence of acting. For animation use believable stylized physics instead of enforcing human photorealism.

## Do not break the old contract
Keep the EXACT 9 labels, their spelling/order and original scene header. No extra keys, numeric label prefixes, summaries, Markdown or machine-incompatible wrapper inside importable TXT. Keep text-to-video independent and do not require reference images. Separate human-readable full screenplay and QC report from prompt-only TXT. Handle long-film continuation without repeating scene IDs or narrative.

## Honest QC
Validate text structure/timecodes first; after rendering inspect each clip for acted motion, physics, lip-sync, identity and duration. Regenerate failing clips only; do not claim image/audio quality proven just because TXT passed.
