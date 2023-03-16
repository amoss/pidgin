# Purpose of unit tests

## unit_seq1

Check behaviour of "any" on a terminal

## unit_seq2

a. Check behaviour of "some" on a terminal (string)
b. Check behaviour of "some" on a terminal (set)

## unit_seq3

a. Check behaviour of greedy "any" on a nonterminal, must be equivalent to unit_seq1
b. Check behaviour of frugal "any" on a nonterminal.
c. Check behaviour of all "any" on a nonterminal.

## unit_seq4

a. Check behaviour of greedy "some" on a nonterminal, must be equivalent to unit_seq2
b. Check behaviour of frugal "some" on a nonterminal.
c. Check behaviour of all "some" on a nonterminal.

## unit_seq5

Check behaviour of "optional" on a nonterminal, wrapping a "some" must be equivalent to unit_seq1

## unit_seq6

Check greediness of "some" on a terminal, ensure overlapping matches in the final symbol are not found.

## unit_seq7

a. Check greediness of "some" on a nonterminal, should be equivalent to unit_seq6.
b. Check frugality of "some" on a nonterminal, should be able to match endings.
b. Check all-matches of "some" on a nonterminal, should be able to match endings.

