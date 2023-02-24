# Types

```
T : {
    integer
    unicode
    boolean
    enum
    [T1 T2 ...]
    ord<T>
    set<T>
    map<T:T>                c( object = map<u[]:T> )
}
```
Type names may be abbreviated to a unique prefix, i.e.

```
some_map = map{ 2:1, 3:3, 4:1 }
a_dict = m{ u[hello] : 2, u(a [) : 7 }
int[1,2,3]
uni[hello world]
uni<hello [world]>
strings = [u[hello] u[world]]
u[Using (] * u([) * u[()]
tags = { u[unicode] u[integer] u[boolean] u[comment] }
```

Commas between elements are optional.


# Patterns

```
modifier = enum{ Any Optional Some Just }
atom<T> : [ seq<T> modifier ] or [ set<T> modifier ]
atom<T> : modifier seq<T> | modifier set<T> | modifier atom<T>
pattern<T> : seq<atom[T]>
```

# Operators

```
s1 = s2      c[ equality ]
len(s1)
set(s)       c[ alphabet ]
set([s])     c[ how to make a set with a single string? ]

-. :: ord<T> ord<T> -> ord<T> boolean       c[ head ]
.- :: ord<T> ord<T> -> ord<T> boolean       c[ pop ]
.+ :: ord<T> ord<T> -> ord<T>               c[ push ]
+. :: ord<T> ord<T> -> ord<T>               c[ insert ]
*  :: ord<T> T -> ord<T>                    c[ join / intersperse ]
/  :: ord<T> T -> ord<ord<T>>               c[ split ]
len :: ord<T> -> int
=  :: T T -> boolean
```

Random examples:
```
u[hello ] + u[world] = u[hello world]

u[some fields,a string,csv] / u[,] = ord< u[some fields], u[a string], u[csv] >
u[some\ttext to\nsplit] / { u[ ], u[\t], u[\n] } = [ u[some], u[text to], u[split] ]
[ u[some fields], u[a string], u[csv] ] * u[,] = u[some fields,a string,csv]

u[string with a suffix] .- u[a suffix] = u[string with a ]
u[prefix on a string] -. u[prefix] = u[ on a string]

            c[ what if there is not the target prefix or suffix? ]

~ :: pattern<T> seq<T> -> boolean
```

# Order indexing and slicing

We need to differentiate between an access to a variable and the use of type tags in constant
expressions, otherwise the set of excluded keywords is huge (because we allow prefixes).

Either we use an explicit symbol to denote array access or the use of brackets needs to be reworked
throughout, and we lose many nice properties.

```
x$[3]
uni$[2,3]
t${7}
slices$<2:3,7:9>
```

# Example code

```
anyPrefixOf(in : ord<uni>) = set{ let n = 1 .. len(in) in in[:n] }
typeNames  = set{
    u[integer]
    u[unicode]
    u[boolean]
    u[enum]
    u[ord]
    u[set]
    u[map]
}
flatten :: set<set{T}> -> set<T>
typePrefixes = flatten . map (anyPrefixOf typeNames)
operators = set{ u[.-], u[.+], u[-.], u[+.], u[*], u[/] }

for each rule in state
    if stack -. rule -> rest {
        reduce by rule
        break
    }
finally
    shift


if seq< Just u[header] Any set(u[+-/]) Optional u[0123456789]> ~ input {
    ....
}
```

# Expression grammar

```
expr : anyDeclaredVar | constant | expr binop expr | func u[(] args u[)]
constant : Some set{012345678}                                                  c( Other bases would be nice here )
         | anyPrefixOf(u[unicode]) u([) Any !set{u(])} u(])
         | anyPrefixOf(u[unicode]) u[(] Any !set{u[)]} u[)]
         | anyPrefixOf(u[unicode]) u[{] Any !set{u[}]} u[}]
         | anyPrefixOf(u[unicode]) u[<] Any !set{u[>]} u[>]
         | anyPrefixOf(u[true])
         | anyPrefixOf(u[false])
         | anyDeclaredEnum
         | anyPrefixOf(u[ord]) u([) Any constant u(])
         | anyPrefixOf(u[ord]) u[(] Any constant u[)]
         | anyPrefixOf(u[ord]) u[{] Any constant u[}]
         | anyPrefixOf(u[ord]) u[<] Any constant u[>]
         | anyPrefixOf(u[set]) u([) Any constant u(])
         | anyPrefixOf(u[set]) u[(] Any constant u[)]
         | anyPrefixOf(u[set]) u[{] Any constant u[}]
         | anyPrefixOf(u[set]) u[<] Any constant u[>]
         | anyPrefixOf(u[map]) u([) Any (constant u[:] constant) u(])
         | anyPrefixOf(u[map]) u[(] Any (constant u[:] constant) u[)]
         | anyPrefixOf(u[map]) u[{] Any (constant u[:] constant) u[}]
         | anyPrefixOf(u[map]) u[<] Any (constant u[:] constant) u[>]
binop : set{ u[.-], u[.+], u[-.], u[+.], u[*], u[/], u[+], u[-], u[@] }
```

# Representing grammars in pidgin

Grammars are an interesting artifact to represent in a data-structure because they mix
text and structure. Looking at two possible syntaxes:


```
{u[expr]:{[T!u[(]NA!u[expr]T!u[)]]}u[lst]:{[NP!u[expr]]}}
{"expr":{[T!"("NA!"expr"T!")"]} "lst":{[NP!"expr"]}}
```

The first keeps the tagged bracketing style for strings, and the second uses standard
double quotes. In both cases the [] {} and {:} symbols have the same meaning, and the
! should be read as application of a function.

A difficulty in reading the second can be seen in `"("NA!"expr"T!` where the single
symbol meaning both "start of a string" and "end of a string" makes it difficult to
read from the middle outwards. For complex structures we end up reading middle-out
because of skimming and skipping.

Although the first form is longer, and we get some collision of symbols because the bounding
brackets for the string occur with other meanings nearby, it is still easier to read
the string/non-string division in `u[(]NA!u[expr]T!`. Using parenthesis for the strings
would avoid the collision with the set/orders in the declaration, but is awkward in this
particular case because of the () within the grammar itself.

A tempting solution is to use “” but they are difficult to type on most keyboards and the
difference is too subtle in most programming fonts. An alternative would be to force the
use of `x´ but this may be awkward to type / remember which order vs ´x`.

```
{`expr´:{[T!`(´NA!`expr´T!`)´]}`lst´:{[NP!`expr´]}}
```

Another alternative is to use both ' and ", as in:
```
{'expr":{[T!'("NA!'expr"T!')"]}'lst":{[NP!'expr"]}}
{'expr": {[ T!'(" NA!'expr" T!')" ]}  'lst": {[ NP!'expr" ]}}
```

# Self-hosting the pidgin grammar

Assuming that we have:
```
T  :: string -> structure
TA :: set(string) -> structure
TAN:: set(string) -> structure       c(Inverse of a character-class any number of times)
TS :: set(string) -> structure
TO :: string -> structure
N  :: string -> structure
NA :: string -> structure
NS :: string -> structure
```

Allowing both the `'"` form and `u()` as an alternative to avoid any escaping rules within strings:
```
pidgin = {
    'expr": { [T!'true"]
              [T!'false"]
              [N!'ident"]
              [N!'number"]
              [N!'str_lit"]
              [N!'set"]
              [N!'map"]
              [N!'order"]
              [N!'bin_op1"]
            }
    'ident": { [T!{'_"'a"'b"'c" ... 'z"'A" ... 'Z"}, TA!{'_"'a"'b"'c" ... 'z"'A" ... 'Z"'0" ... '9"}] }
    'number": { [TS!{'0"...'9"}] }
    'str_list": { [T!u('), TAN!u("), T!u(")]
                  [T!'u(", TAN!')",  T!')"]
                }
    'set":   { [T!'{",  NA!'expr_lst",  T!'}”] }
    'order": { [T!'[",  NA!'expr_lst",  T!']"] }
    'map":   { [T!'{",  NA!'expr_kv",   T!'}"] }
    'expr_lst": { [N!'expr",  TO!',"] }
    'expr_kv":  { [N!'expr",  T':",  N!'expr",  TO!',"] }
    'binop1":     { [N!'binop2",  NS!'binop1_lst"] }
    'binop1_lst": { [T!'.+",  N!'binop2"]
                    [T!'+.",  N!'binop2"]
                    [T!'.-",  N!'binop2"]
                    [T!'-.",  N!'binop2"]
                    [T!'-",   N!'binop2"]
                    [T!'+",   N!'binop2"]
                  }
    'binop2":     { [N!'binop3", NS!'binop2_lst"] }
    'binop2_lst": { [T!'*",      NS!'binop3"]
                    [T!'/",      NS!'binop3"]
                  }
    'binop3:      { [N!'expr",   NA!'binop3_lst"] }
    'binop3_lst": { [T!'@",      N!'expr"] }

}
```

Currently there are at least these issues with the self-hosting grammar:

1. The number of arguments is not specified anywhere.
1. The functors and their application symbol `!` are not in the grammar.
1. Parenthesis are not in expression yet.
1. The keywords `true` and `false` are not excluded from the set of identifiers.












