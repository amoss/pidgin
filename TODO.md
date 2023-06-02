Short-term
-----------

* Add an entry point definition.
* Work out how to handle implicit function wrapper for top-level statements.
* Provide access to stdin.
* Add an output/print statement.
* Add conditionals.
* Add if-then-else statements, extend basic block translation.
* Add a for-each loop that can iterate over sequences and sets.
* Handle SSA properly, respect last def of variables, introduce phi-nodes.
* Fill out set of operators and their implementations.
* Write a test-suite of simple programs, extend the test runner to handle.
* Add patterns to the language.
* Start reworking the ECLR parsing algorithm in pidgin.

Long-term
---------

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

