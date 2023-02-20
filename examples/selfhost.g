GRAMMAR:      RULE+ ;
RULE:         RuleMod? Ident WhiteSp* ":" WhiteSp* CLAUSES WhiteSp* ";" WhiteSp* ;
RuleMod:      [+-];
CLAUSES:      CLAUSE MORECLAUSES* ;
MORECLAUSES:  "|" CLAUSES ;
CLAUSE:       SYMB MORESYMBS* ;
MORESYMBS:    WhiteSp+ SYMB ;
SYMB:         Ident Suffix? | Regex+ | LitString ;

WhiteSp:    [ \t\n];
Ident:      [A-Z] [A-Za-z0-9_]* ;
Suffix:     "?" | "*" | "+" ;
LitString:  ["] LitAtom+ ["] ;
LitAtom:    "\\\\" | "\\n" | "\\t" | [^"\\] ;

Regex:      RegExAtom Suffix? ;
RegExAtom:  "[" ClassAtom+ "]" ;
ClassAtom:  "0-9" | "a-z" | "A-Z" | "\\]" | "\\^" | "\\-" | "\\" | [^\\\]] ;


