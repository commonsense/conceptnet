Document types
--------------

Assertions
..........

Unique together:

- dataset [Dataset]: what project does this assertion come from?
- relation [Relation]: IsA, PartOf, ...
- arguments [list(Concept)]: the concepts that fill these slots. Could be null.
  In ConceptNet 5 assertions, argument 0 is reserved for "context".
- polarity [bool]: True for positive statements, False for negative

Other information:

- justifications [tree]: an AND/OR tree of reasons we believe it. The leaves
  of this tree are sub-documents with no rigid schema.
- expressions [list]: list of sub-documents saying how to express this in
  natural language
- updated_at [timestamp]

Derived fields:

- complete [bool]: True if complete assertion, False if feature/template
- confidence [float?]: generated from justifications

Expressions
```````````
Each Assertion contains some number of Expressions within its document, with
the following information:

- language [string]: ISO code
- question [bool]: True if question form, False otherwise
- assertion [Assertion as objectID]
- text [string]: can have {0}, {1}, {2}, etc. blanks for incomplete docs

Concepts
........

Unique together:

- representation [str+index]: Specifies how to interpret the concept -- as
  an English lemma, an English WordNet sense, a Cyc identifier...
- text [string]: the concept's identifier in that representation

Other information:

- num_assertions [int]: how many assertions we have about the concept
- updated_at [timestamp]

"Representations" are just strings that describe a path from least- to
most-specific. Examples:

- lemma/en/conceptnet/5
- word_sense/en/wordnet/3
- lemma/en/wordnet/3
- cycl/opencyc

Relations
.........

- name [str]: PartOf, IsA, etc.
- arguments: list of (argname, type), specifying what each argument means
  and what type of thing it wants to fill that slot.

Datasets
........

Each Dataset is downloaded separately, and possibly maintained by separate
groups.

Unique:

- id [string]: for example, "conceptnet/en"
- version [string]: the version number of the currently-installed dataset
- url [string]: where to access metadata about the dataset


LogEntries
..........

- object_id [object]: which object is affected
- action [string]: what happened in general
- data [dict]: Together with the action, specifies what happened in
  particular. No particular schema is enforced on it.
- time [timestamp]



