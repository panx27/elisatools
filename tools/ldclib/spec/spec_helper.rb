$:.push File.expand_path('../../lib', __FILE__)

require 'ostruct'

YAML1 = '---
version: 1
words: {}
transitions:
- noun
- noun plural
morphemes:
  noun:
  - test
  plural:
  - s
'
YAML2 = '---
version: 2
words: {}
transitions:
- noun
- noun plural
morphemes:
  noun:
    test: {}
  plural:
    s: {}
'
YAML3 = '---
version: 3
words:
  noun:
    pos: NOUN
  noun plural.s:
    pos: NOUN
  noun.es pl.es:
    pos: NOUN
  verb:
    pos: VERB
  verb2:
    pos: VERB
morphemes:
  noun:
    morph: n
    strings:
      test:
        morph: nn
        lemma: tt
      fest: {}
  noun.es:
    morph: noun
    strings:
      match: {}
      batch: {}
  det:
    strings:
      the: {}
  plural.s:
    morph: plural
    strings:
      s: {}
  pl.es:
    morph: pl
    strings:
      es: {}
  verb:
    strings:
      see: {}
  verb2:
    morph: verb
    strings:
      saw: {}
'
YAML4 = '---
version: 4
words:
  noun: NOUN
  noun s=plural: NOUN
  noun.es es=pl: NOUN
morphemes:
  noun:
  - test:tt=nn
  - fest
  noun.es:
  - match
  - batch
  det:
  - the
morph_tags:
  noun: n
'
YAML5 = '---
- version 5
- pos:NOUN noun
- pos:NOUN noun s=plural
- pos:NOUN noun.es es=pl
- morph:noun n
- m:noun test:tt=nn
- m:noun fest
- m:noun.es match
- m:noun.es batch
- m:det the
'
YAML3_from_4 = '---
version: 3
words:
  noun:
    pos: NOUN
  noun plural:
    pos: NOUN
morphemes:
  noun:
    strings:
      test: {}
  plural:
    strings:
      s: {}
'
YAML4_from_3 = '---
version: 4
words:
  noun: X
  noun plural: X
morphemes:
  noun:
  - test:test=noun
  plural:
  - s
'
# the following shows some error conditions
# 1. string specific pos
# 2. morpheme level lemma
YAML_BAD = '---
version: 3
words:
  noun: {}
  noun plural: {}
morphemes:
  noun:
    pos: noun
    lemma: noun
    strings:
      test:
        pos: noun
  plural:
    strings:
      s: {}
'
