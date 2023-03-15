# Purpose of unit tests

## unit_seq1

Check behaviour of "any" on a terminal

## unit_seq2

Check behaviour of "some" on a terminal

## unit_seq3

Check behaviour of "any" on a nonterminal, must be equivalent to unit_seq1

## unit_seq4

Check behaviour of "some" on a nonterminal, must be equivalent to unit_seq2

## unit_seq5

Check behaviour of "optional" on a nonterminal, wrapping a "some" must be equivalent to unit_seq1

## unit_seq6

Check greediness of "some" on a terminal, ensure overlapping matches in the final symbol are not found.

## unit_seq7

Check greediness of "some" on a nonterminal, must be equivalent to unit_seq6

