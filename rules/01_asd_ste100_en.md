# ASD-STE100 Rules for Agent Instructions & English Scripts (`01_rules/01_asd_ste100_en.md`)

Apply Simplified Technical English (ASD-STE100) to:
- Agent system prompts (`AGENTS.md`, `03_skills/*/SKILL.md`)
- CLI help strings, validation errors, and status logs
- Spoken English voiceover scripts (`script.json` narration)

## Six Core Constraints

1. **One Instruction Per Sentence**: Write one action per sentence. Keep procedural sentences at 20 words or fewer.
2. **Active Voice Only**: Name the actor and verb clearly.
   - Do: `Run "vc validate" before you synthesize audio.`
   - Do not: `Validation should be run prior to audio synthesis.`
3. **Use Approved One-Meaning Verbs**: Pick one verb for one meaning across all files.
   - `Run` (execute a command), `Open` (load a file or UI), `Set` (assign a parameter), `Check` (verify a condition), `Stop` (halt on error).
   - Avoid synonyms like `execute`, `trigger`, `fire`, `leverage`, `utilize`, `facilitate`.
4. **Cut Hedge and Filler Words**: Remove `basically`, `actually`, `simply`, `robust`, `seamless`, `in order to`, `please note that`.
5. **Define Technical Terms Once**: Introduce each domain term cleanly before first use (enforced by `script.json` `glossary`).
6. **Prevent Noun Stacks**: Limit noun clusters to at most three nouns.
   - Do: `the shell thickness table`
   - Do not: `the automated batch shell geometry validation thickness configuration table`

## Pipeline Enforcement in `vc/script.py`

`python -m vc validate` enforces four ASD-STE100 metrics automatically:
- `max_sentence_words`: Default `20` words per sentence.
- `max_fk_grade`: Flesch-Kincaid Grade Level `<= 8.0`.
- `glossary`: Term order check (`defined_in` scene ID).
- `banned_terms`: Rejects vague marketing adjectives (`robust`, `seamless`, `watertight`) and cryptic jargon (`t/2`).
