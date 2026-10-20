# Star Wars Database

## CSV Layout

- `database/entities.csv` merges every record into one table. It has
  common columns (`id`, `entity_type`, `category`, `collection`,
  `title`, `description`, `history`, and image fields) followed by the union of
  SWAPI fields. Category and collection make the records filterable without
  separate folders. List-valued SWAPI attributes are JSON-encoded in their cell.
- `database/entity_aliases.csv` maps former entity IDs to one canonical entity
  and archives the merged record as JSON. Aliases are not separate entities;
  the wiki resolves old entity URLs to their canonical page.
- `database/entity_images.csv` stores ordered images as `(entity_id, position,
  path, status)`. Each row references one entity; add rows with increasing
  positions to attach additional images. Existing primary image fields remain
  in `entities.csv` for compatibility; the image table is authoritative for
  entity pages.
- `database/IDENTITY_AUDIT.md` records the identity merge checks, results, and
  cases kept separate because they represent different entities.
- `database/metadata.csv` stores repeatable databank metadata as
  `(entity_id, field, value, related_entity_id)`.
- `database/relationships.csv` stores internal entity links such as film
  membership, pilots, homeworlds, and exact cross-source identity matches as
  `(source_id, relationship, target_id)`.
- `database/timeline_events.csv` stores ordered lore events with stable event
  IDs, order, and display fields used by the starter timeline.
- `database/timeline_entities.csv` links timeline events to database entities
  as `(event_id, entity_id, relationship)`. Links include Databank collection
  and appearance metadata, plus SWAPI film membership.
- `database/timeline_scenes.csv` stores screenplay scene headings and their
  order within each film event. `location_entity_id` is populated when a scene
  heading names a known location.
- `database/timeline_scene_entities.csv` links scenes to matched location and
  vehicle entities.
- `database/quotes.csv` stores dialogue rows with their screenplay order,
  scene, speaker label, and matched `speaker_entity_id` when the label resolves
  to a character record. Unmatched speaker labels remain available as text.
- `entities.csv` retains the original `image_path` and `image_status` fields.
  `entity_images.csv` contains the corresponding first image for every entity.
  Image paths are relative to `database/`; copied card assets live in
  `database/images` and use entity-ID-based unique filenames. Entries without
  source art use `placeholder` status and point to `images/z-placeholder-img.png`.

All imported values and relationships live in `database/`; no entity depends
on a source folder. IDs retain their original namespaces as stable identifiers:
databank IDs use
`databank:<databank-folder>:<category>:<slug>` and SWAPI IDs use
`swapi:<resource>:<source-pk>`. Treat IDs as opaque strings. Foreign keys in
`relationships.csv`, `metadata.csv`, and `timeline_entities.csv` reference
entity IDs from `entities.csv`. Alias IDs in `entity_aliases.csv` resolve to
those canonical entity IDs. Timeline event IDs match the starter timeline
IDs (for example, `phantom-menace`); `sequence` is chronological order and
`year` uses BBY/ABY with 0 as the Battle of Yavin. `previous_event_id` links
events within `timeline_events.csv`.

## Sources

Source #1:
https://www.starwars.com/databank/star-wars-prequel-trilogy-all
The Phantom Menace (155)
Attack of the Clones (186)
Revenge of The Sith (181)

Source #2:
https://www.starwars.com/databank/star-wars-original-trilogy-all
A New Hope (122)
The Empire Strikes Back (95)
Return of the Jedi (161)

Source #3:
https://github.com/api-evangelist/swapi

Source #4:
https://github.com/Juriy/swapi

Source #5:
https://github.com/itwasmattgregg/Star-Wars-Timeline (dumb timeline)

Source #6:
https://github.com/jcwieme/data-scripts-star-wars (movie dialogue for quotes!)

## Notes

Timeline/Lore
Planets
Images!!

The Phantom Menace
Attack of the Clones
Revenge of The Sith
A New Hope
The Empire Strikes Back
Return of the Jedi
