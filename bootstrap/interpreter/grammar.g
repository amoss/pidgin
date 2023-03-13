{
    'program": { [NS!'decl"] }
    'decl": { [T!'func" N!'ident" N!'record_decl" T!'{" NS!'statement" T!'}"]
              [N!'enum_decl"]
            }
    'record_decl": { [T!'[" NS!'nametype" T!']" ] }
    'enum_decl": { [T!'enum" N!'ident" T!'[" NS!'ident" T!']"] }
    'statement": { [T!'return" N!'expr" ]
                   [N!'ident"  T!'=" N!'expr"]
                 }
    'nametype":  { [N!'ident" T!':" N!'type_decl"] }
    'type_decl": { [T!'int"]
                   [T!'string"]
                   [T!'set<"   N!'type_decl" T!'>"]
                   [T!'map<"   N!'type_decl" N!'type_decl" T!'>"]
                   [T!'order<" N!'type_decl" T!'>"]
                 }

    'expr": { [N!'binop1"] }
    'binop1":     { [N!'binop2",  NA!'binop1_lst"] }
    'binop1_lst": { [T!'.+",  N!'binop2"]
                    [T!'+.",  N!'binop2"]
                    [T!'.-",  N!'binop2"]
                    [T!'-.",  N!'binop2"]
                    [T!'-",   N!'binop2"]
                    [T!'+",   N!'binop2"]
                  }
    'binop2":     { [N!'binop3", NA!'binop2_lst"] }
    'binop2_lst": { [T!'*",      N!'binop3"]
                    [T!'/",      N!'binop3"]
                  }
    'binop3":     { [N!'binop4",   NA!'binop3_lst"] }
    'binop3_lst": { [T!'@",        N!'binop4"] }
    'binop4":     { [N!'ident",    T!'!",   N!'atom"]
                    [N!'atom"]
                  }
    'atom": { [T![chars:'true" tag:'bool"]]
              [T![chars:'false" tag:'bool"]]
              [N!'ident"]
              [N!'number"]
              [N!'str_lit"]
              [N!'set"]
              [N!'map"]
              [N!'order"]
              [N!'record"]
              [T!'(",  N!'expr",  T!')"]
            }
    'ident": { [T![chars:{'A" 'B" 'C" 'D" 'E" 'F" 'G" 'H" 'I" 'J"
                          'K" 'L" 'M" 'N" 'O" 'P" 'Q" 'R" 'S" 'T"
                          'U" 'V" 'W" 'X" 'Y" 'Z"
                          'a" 'b" 'c" 'd" 'e" 'f" 'g" 'h" 'i" 'j"
                          'k" 'l" 'm" 'n" 'o" 'p" 'q" 'r" 's" 't"
                          'u" 'v" 'w" 'x" 'y" 'z"
                          '_"} tag:'ident"],
                G!'",
                TA!{'A" 'B" 'C" 'D" 'E" 'F" 'G" 'H" 'I" 'J"
                    'K" 'L" 'M" 'N" 'O" 'P" 'Q" 'R" 'S" 'T"
                    'U" 'V" 'W" 'X" 'Y" 'Z"
                    'a" 'b" 'c" 'd" 'e" 'f" 'g" 'h" 'i" 'j"
                    'k" 'l" 'm" 'n" 'o" 'p" 'q" 'r" 's" 't"
                    'u" 'v" 'w" 'x" 'y" 'z"
                    '_" '0", '1", '2", '3", '4", '5", '6", '7", '8", '9"},
                R!'"]
             }
    'number": { [TS![chars:{'0", '1", '2", '3", '4", '5", '6", '7", '8", '9",} tag:'num"]] }
    'str_lit": { [T!u('), G!'", TAN!{u(")}, T!u(")]
                 [T!'u(", G!'", TAN!{')"},  T!')"]
               }
    'set":   { [T!'{",  NO!'elem_lst",  T!'}"] }
    'map":   { [T!'{",  NS!'elem_kv",   T!'}"]
               [T!'{",  T!':",          T!'}"] }
    'order": { [T!'[",  NO!'elem_lst",  T!']"] }
    'record": { [T!'[",  NS!'elem_iv",   T!']"]
                [T!'[",  NS!'elem_anonv", T!']"]}

    'elem_kv":  { [N!'expr",  T!':",  N!'expr",  TO!',"] }
    'elem_iv":  { [N!'ident",  T!':",  N!'expr",  TO!',"] }
    'elem_anonv":  { [T!':",  N!'expr",  TO!',"] }
    'elem_lst": {[NA!'repeat_elem", N!'final_elem"]}
    'repeat_elem": {[N!'expr", G!'", T!{' " '	" '" ',"}]}
    'final_elem": {[N!'expr", G!'", TO!{' "  '	" '" ',"}]}

}

