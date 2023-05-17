
## toy_numberlist
`Test lists of integer literals.`


![eclr machine](toy_numberlist/eclr.dot.png)

## toy_stringlist
`atom: str_lit | order   order: [ elem_lst* ]   elem_lst: atom?   str_lit: ' [^"]* " | u( [^)]* )`
       Test lists of pidgin-style string literals.

![eclr machine](toy_stringlist/eclr.dot.png)

## toy_stringlist2
`A: S | O   O: [ ] | [ P* A ,?] | [ A A+ ]   P: A ,   S: ' [^"]* " | u( [^)]* )`
       Test lists of pidgin-style string literals with uniform but optional commas.

![eclr machine](toy_stringlist2/eclr.dot.png)

## quoted_str
`Q: ' [^"]* " | u( [^)]* \)`
       Test inverted character sets and glue.

![eclr machine](quoted_str/eclr.dot.png)

## quoted_str2
`Q: ' [^"]* " | << ([^>] | > [^>])* >>`
       Test inverted character sets and glue, matching a two-symbol terminator.

![eclr machine](quoted_str2/eclr.dot.png)

## quoted_str3
`Q: " ([^"] | \ [^] )* "`
       Test C-style strings with two-symbol escape sequences.

![eclr machine](quoted_str3/eclr.dot.png)

## quoted_str4
`L: I  | I ! L | Q    Q: ' [^"]* " | u( [^)]* \)    I: [a-z] Glue [a-z0-9]* Remover`
       Test pidgin-style strings in a language with a single binary operator.

![eclr machine](quoted_str4/eclr.dot.png)

## quoted_str5
`Binop: I ! Binop | Atom   Atom: I | Q    Q: ' [^"]* " | u( [^)]* \)    I: [a-z] Glue [a-z0-9]* Remover`
       Test pidgin-style strings in a language with a single binary operator. Differs to the previous
       case by splitting the ident and indent-plus-operator into separate rules to simulate a piece
       of the pidgin grammar.

![eclr machine](quoted_str5/eclr.dot.png)

## recurse_degenseq
`R: R* x`
       Test degenerate form of terminal repetition, same language as x+ but combinatorially ambiguous without
       greediness. Left-recursive form.

![eclr machine](recurse_degenseq/eclr.dot.png)

## recurse_degenseq2
`R: x R*`
       Test degenerate form of terminal repetition, same language as x+ but combinatorially ambiguous without
       greediness. Right-recursive form.

![eclr machine](recurse_degenseq2/eclr.dot.png)

## recurse_degenseq3
`R: (R x)*`
       Test degenerate form of terminal repetition, same language as x* but combinatorially ambiguous without
       greediness. Left-recursive form. Successful traces have a prefix that reduces empty to R before starting
       to shift.

![eclr machine](recurse_degenseq3/eclr.dot.png)

## recurse_degenseq4
`R: (x R)*`
       Test degenerate form of terminal repetition, same language as x* but combinatorially ambiguous without
       greediness. Right-recursive form.

![eclr machine](recurse_degenseq4/eclr.dot.png)

## recurse_nests
`R: l R* r`
       Test bracket nesting. Not degenerate as sub-sequences cannot overlap?

![eclr machine](recurse_nests/eclr.dot.png)

## recurse_nests2
`R: (l R r)*`
       Test bracket nesting. Not degenerate as sub-sequences cannot overlap?

![eclr machine](recurse_nests2/eclr.dot.png)

## recurse_parensseq
`E: (x | < E >)(+ E)*`
       Test a parenthesized sequence with a single operator.

![eclr machine](recurse_parensseq/eclr.dot.png)

## recurse_parensseq2
`E: F (/ F)* ; F: (x | < E >)(+ E)*`
       Test a parenthesized sequence with two prioritized operators.

![eclr machine](recurse_parensseq2/eclr.dot.png)

## recurse_partialnests
`R: l* R r*`
       Test bracket (partial-) nesting. Impossible to match as requires an infinitely deep
       nesting of R.

![eclr machine](recurse_partialnests/eclr.dot.png)

## recurse_termplusvianonterm
`R: S* x ; S: x`
       Test that non-terminal stars are equivalent to terminal stars, simulate x+ via depth-limited recursion.

![eclr machine](recurse_termplusvianonterm/eclr.dot.png)

## recurse_termplusvianonterm2
`R: S* l r ; S: l r`
       Test that non-terminal stars are equivalent to terminal stars, simulate (l r)+ via depth-limited recursion.

![eclr machine](recurse_termplusvianonterm2/eclr.dot.png)

## regex_choice
`R: (x|y) (y|z) (z|k)`
       Test sequence of choices with overlapping cases.

![eclr machine](regex_choice/eclr.dot.png)

## regex_choicestar
`R: (x|y)* (y|z)* (z|k)*`
       Test sequence of repeated choices with overlapping cases.

![eclr machine](regex_choicestar/eclr.dot.png)

## regex_glue
`R: [a-z] Glue [a-z0-9]* Remover`
       Test use of glue between terminals.

![eclr machine](regex_glue/eclr.dot.png)

## regex_glue2
`R: [a-z] Glue [a-z0-9]* Remover`
       Test use of glue between terminals.

![eclr machine](regex_glue2/eclr.dot.png)

## regex_selfalignboundedboth
`R: l (x y)* r`
       Test self aligned repeating sequence with a non-overlapping boundary on both sides.

![eclr machine](regex_selfalignboundedboth/eclr.dot.png)

## regex_selfalignboundedboth2
`R: x (x y)* x`
       Test self aligned repeating sequence with an overlapping boundary on both sides.

![eclr machine](regex_selfalignboundedboth2/eclr.dot.png)

## regex_selfalignboundedleft
`R: l (x y)*`
       Test self aligned repeating sequence with a non-overlapping boundary on the left.

![eclr machine](regex_selfalignboundedleft/eclr.dot.png)

## regex_selfalignboundedleft2
`R: x (x y)*`
       Test self aligned repeating sequence with an overlapping boundary on the left.

![eclr machine](regex_selfalignboundedleft2/eclr.dot.png)

## regex_selfalignboundedright
`R: (x y)* r`
       Test self aligned repeating sequence with a non-overlapping boundary on the right.

![eclr machine](regex_selfalignboundedright/eclr.dot.png)

## regex_selfalignboundedright2
`R: (x y)* x`
       Test self aligned repeating sequence with an overlapping boundary on the right.

![eclr machine](regex_selfalignboundedright2/eclr.dot.png)

## regex_selfalignunbounded
`R: (x y)*`
       Test self aligned repeating sequence with no boundaries.

![eclr machine](regex_selfalignunbounded/eclr.dot.png)

## regex_seq
`R: x y z`
       Test sequencing of terminals in a grammar.

![eclr machine](regex_seq/eclr.dot.png)

## regex_seqstar
`R: x* y* z*`
       Test repetition of terminals within a sequence.

![eclr machine](regex_seqstar/eclr.dot.png)

## regex_starboundedboth
`R: l x* r`
       Test repetition of a terminal with a non-overlapping boundary on both sides.

![eclr machine](regex_starboundedboth/eclr.dot.png)

## regex_starboundedboth2
`R: x x* x`
       Test repetition of a terminal with an overlapping boundary on both sides.

![eclr machine](regex_starboundedboth2/eclr.dot.png)

## regex_starboundedleft
`R: l x*`
       Test repetition of a terminal with a non-overlapping boundary on the left.

![eclr machine](regex_starboundedleft/eclr.dot.png)

## regex_starboundedleft2
`R: x x*`
       Test repetition of a terminal with an overlapping boundary on the left.

![eclr machine](regex_starboundedleft2/eclr.dot.png)

## regex_starboundedleft3
`R: x W ; W: x*`
       Test repetition of a terminal with an overlapping boundary on the left, where the repeating part is
       wrapped inside a non-terminal to test if the handle check consumes the extra symbol.

![eclr machine](regex_starboundedleft3/eclr.dot.png)

## regex_starboundedright
`R: x* r`
       Test repetition of a terminal with a non-overlapping boundary on the right.

![eclr machine](regex_starboundedright/eclr.dot.png)

## regex_starboundedright2
`R: x* x`
       Test repetition of a terminal with an overlapping boundary on the right, equivalent to x+

![eclr machine](regex_starboundedright2/eclr.dot.png)
