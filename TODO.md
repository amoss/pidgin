Short-term
-----------

* Add multiple outputs for instructions (so that iterators can be handled correctly).
* Expand the set of tests to cover the SSA generation.
* Fill out set of operators and their implementations.
* Add implicit threading of stdin/stdout to translation and type-checking.
  Rework input to match, add stream/channel types and remove the string input
  at the beginning.
* Write a test-suite of simple programs, extend the test runner to handle.
* Add patterns to the language.
* Start reworking the ECLR parsing algorithm in pidgin.

Long-term
---------

* Add location information to parser tokens.
* Error handling for ECLR. Rough idea is that if the parse fails then we walk
  back through the configurations where the parser blocked and work out how
  to repair the parse. Repair should be a combination of popping tokens off the
  stack and skipping characters in the input. After repair the resulting
  tree(s) will feature error nodes where the popped tokens would have been.
* Transliteration into C, javascript.
* Conversion to c++ / llvm (use a transliterated parser as the front-end).
* Compilation into native code.
* Run-time for strings as collection of extents.

Open questions
--------------

* How should the parts of the parser be structured in the language to access
  as first-class primitives?
* How should generation be handled for ECLR (i.e. do some experiments on tree
  generation to work out how to adaptively shape trees from bias parameters and
  convert to sampling of grammars).

