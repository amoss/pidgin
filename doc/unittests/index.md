
## regex_seq
`R: x y z`
       Test sequencing of terminals in a grammar.

![eclr machine](regex_seq/eclr.dot.png)

## regex_seqstar
`R: x* y* z*`
       Test repetition of terminals within a sequence.

![eclr machine](regex_seqstar/eclr.dot.png)

## regex_starboundedleft
`R: l x*`
       Test repetition of a terminal with a non-overlapping boundary on the left.

![eclr machine](regex_starboundedleft/eclr.dot.png)

## regex_starboundedleft2
`R: x x*`
       Test repetition of a terminal with an overlapping boundary on the left.

![eclr machine](regex_starboundedleft2/eclr.dot.png)

## regex_starboundedright
`R: x* r`
       Test repetition of a terminal with a non-overlapping boundary on the right.

![eclr machine](regex_starboundedright/eclr.dot.png)

## regex_starboundedright2
`R: x* x`
       Test repetition of a terminal with an overlapping boundary on the right.

![eclr machine](regex_starboundedright2/eclr.dot.png)

## regex_starboundedboth
`R: l x* r`
       Test repetition of a terminal with a non-overlapping boundary on both sides.

![eclr machine](regex_starboundedboth/eclr.dot.png)

## regex_starboundedboth2
`R: x x*`
       Test repetition of a terminal with an overlapping boundary on both sides.

![eclr machine](regex_starboundedboth2/eclr.dot.png)

## regex_choice
`R: (x|y) (y|z) (z|k)`
       Test sequence of choices with overlapping cases.

![eclr machine](regex_choice/eclr.dot.png)

## regex_choicestar
`R: (x|y) (y|z) (z|k)`
       Test sequence of repeated choices with overlapping cases.

![eclr machine](regex_choicestar/eclr.dot.png)

## regex_selfalignunbounded
`R: (x y)*`
       Test self aligned repeating sequence with no boundaries.

![eclr machine](regex_selfalignunbounded/eclr.dot.png)

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

## regex_selfalignboundedboth
`R: l (x y)* r`
       Test self aligned repeating sequence with a non-overlapping boundary on both sides.

![eclr machine](regex_selfalignboundedboth/eclr.dot.png)

## regex_selfalignboundedboth2
`R: x (x y)* x`
       Test self aligned repeating sequence with an overlapping boundary on both sides.

![eclr machine](regex_selfalignboundedboth2/eclr.dot.png)
