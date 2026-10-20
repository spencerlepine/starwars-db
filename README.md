# Star Wars Database

## CSV Layout

- `mono-database/entities.csv` merges every record into one table. It has
  common columns (`id`, `source`, `entity_type`, `category`, `collection`,
  `title`, `description`, `history`, image fields, and source path) followed by
  the union of source-specific SWAPI fields. Category and collection make the
  records filterable without separate folders. List-valued SWAPI attributes
  are JSON-encoded in their cell.
- `mono-database/metadata.csv` stores repeatable databank metadata as
  `(entity_id, field, value, related_entity_id)`.
- `mono-database/relationships.csv` stores foreign keys such as film characters
  and a person's homeworld as `(source_id, relationship, target_id)`.
- Every entity has `image_path` and `image_status` in `entities.csv`. Existing
  databank card images use relative paths and `available` status; records
  without images have a blank path and `placeholder` status.

IDs are source-namespaced: databank IDs use
`databank:<databank-folder>:<category>:<slug>` and SWAPI IDs use
`swapi:<resource>:<source-pk>`. Treat IDs as opaque strings. Foreign keys in
`relationships.csv` and `metadata.csv` reference these IDs.

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

## Notes

Timeline/Lore
Planets
Images!!