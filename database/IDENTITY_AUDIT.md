# Entity identity audit

This audit covers the merged six-film Databank and SWAPI records in this
directory. It was run after the character and cross-category merge passes.

## How identity was checked

- Compared normalized titles across every category and film collection.
- Applied the database's curated `same_as` links, then replaced those links
  with canonical entity IDs.
- Reviewed source naming and model variants that exact title matching misses,
  including `Yavin IV` / `Yavin 4`, `Wookie` / `Wookiee`, `Neimodian` /
  `Neimoidian`, `Scimitar` / `Sith Infiltrator`, and `Slave 1` / Boba Fett's
  starship.
- Repointed relationship, metadata, quote, timeline, and scene references to
  the canonical IDs. `entity_aliases.csv` retains each former ID and its full
  original record as JSON; wiki requests for old entity URLs resolve to the
  canonical entity.

## Results

- 594 canonical entity rows and 566 archived aliases account for all 1,160
  original entity records.
- No repeated normalized titles remain within a category, and no exact title
  is shared across categories.
- No `same_as` relationships remain because confirmed identity links are now
  represented by a single entity row.
- All checked entity foreign keys, timeline event links, alias targets, and
  image paths resolve.

## Identity boundary

Similar records can still represent different things. For example, a CR90
corvette is a ship class while the Tantive IV is one ship of that class;
Belbullab-22 is a starfighter model while the Soulless One is a named craft;
and LAAT/i and LAAT/c are distinct variants. These remain separate entities.
SWAPI records without a matching Databank identity also remain standalone.

Title scans cannot prove that every differently named record is the same
identity. New imported sources should be checked for alternate names and model
fields, with confirmed matches added to the canonical entity and recorded in
`entity_aliases.csv`.
