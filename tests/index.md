# Purpose of unit tests

## unit_seq1

Check behaviour of "any" on a terminal

## unit_seq2

<ol type="a">
    <li>Check behaviour of "some" on a terminal (string)</li>
    <li>Check behaviour of "some" on a terminal (set)</li>
</ol>

## unit_seq3

<ol type="a">
    <li>Check behaviour of greedy "any" on a nonterminal, must be equivalent to unit_seq1</li>
    <li>Check behaviour of frugal "any" on a nonterminal.</li>
    <li>Check behaviour of all "any" on a nonterminal.</li>
</ol>

## unit_seq4

<ol type="a">
    <li>Check behaviour of greedy "some" on a nonterminal, must be equivalent to unit_seq2.</li>
    <li>Check behaviour of frugal "some" on a nonterminal.</li>
    <li>Check behaviour of all "some" on a nonterminal.</li>
</ol>

## unit_seq5

Check behaviour of "optional" on a nonterminal, wrapping a "some" must be equivalent to unit_seq1

## unit_seq6

Check greediness of "some" on a terminal, ensure overlapping matches in the final symbol are not found.

## unit_seq7

<ol type="a">
    <li>Check greediness of "some" on a nonterminal, should be equivalent to unit_seq6.</li>
    <li>Check frugality of "some" on a nonterminal, should be able to match endings.</li>
    <li>Check all-matches of "some" on a nonterminal, should be able to match endings.</li>
</ol>

## unit_seq8

<ol type="a">
    <li>Check nesting of greedy nonterminal "any" inside of greedy nonterminal "some"</li>
    <li>Check nesting of frugal nonterminal "any" inside of greedy nonterminal "some"</li>
    <li>Check nesting of all nonterminal "any" inside of greedy nonterminal "some"</li>
    <li>Check nesting of greedy nonterminal "any" inside of frugal nonterminal "some"</li>
    <li>Check nesting of frugal nonterminal "any" inside of frugal nonterminal "some"</li>
    <li>Check nesting of all nonterminal "any" inside of frugal nonterminal "some"</li>
    <li>Check nesting of greedy nonterminal "any" inside of all nonterminal "some"</li>
    <li>Check nesting of frugal nonterminal "any" inside of all nonterminal "some"</li>
    <li>Check nesting of all nonterminal "any" inside of all nonterminal "some"</li>
</ol>

## unit_seq9

<ol type="a">
    <li>Check nesting of greedy nonterminal "some" inside of greedy nonterminal "any"</li>
    <li>Check nesting of frugal nonterminal "some" inside of greedy nonterminal "any"</li>
    <li>Check nesting of all nonterminal "some" inside of greedy nonterminal "any"</li>
    <li>Check nesting of greedy nonterminal "some" inside of frugal nonterminal "any"</li>
    <li>Check nesting of frugal nonterminal "some" inside of frugal nonterminal "any"</li>
    <li>Check nesting of all nonterminal "some" inside of frugal nonterminal "any"</li>
    <li>Check nesting of greedy nonterminal "some" inside of all nonterminal "any"</li>
    <li>Check nesting of frugal nonterminal "some" inside of all nonterminal "any"</li>
    <li>Check nesting of all nonterminal "some" inside of all nonterminal "any"</li>
</ol>

# Second batch of unit tests


## Recursive cases

R: S* x ; S: x
R: S* l r ; S: l r
E: (x | < E >)(+ E)*
E: F(/ F)* ; F: (x | < E >)(+ F)*
