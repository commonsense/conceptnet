Ideas for representing ConceptNet without SQL
=============================================

Document types
--------------

Edge:

- type: 'assertion', 'statement', 'dependency', ...
- dataset: language
- text: best sentence, with [[links]]
- nodes: list of at least 2 concepts
- relation: IsA, PartOf, ...
- frame: (objectID or null)
- justifications: an AND/OR tree of reasons to believe it
- confidence: generated from justifications
- frequency: -10 to 10
- weight: generated from confidence and frequency
- valid: T/F
- log: (list of [timestamp, description])

Concept:

- type: 'concept'
- id: (normalized name)
- text: (best un-normalized name)
- dataset: language
- edges: (list)
- valid: T/F

Sentence:

- type: 'sentence'
- dataset
- tokens: (list)
- valid: T/F
- confidence
- justifications

Frame:

- text: has {1} and {2} blanks
- goodness: 1-3
- relation: IsA, PartOf, ...
- frequency: -10 to 10

