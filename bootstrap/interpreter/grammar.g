{
    'program": { [NS!'decl"] }
    'decl": { [T!'func" N!'ident" T!':" N!'type_decl" N!'record_decl" T!'{" NS!'decl" T!'}"]
              [N!'enum_decl"]
              [N!'statement"]
              [T!'type" N!'ident" T!':" N!'type_decl"]
            }
    'record_decl": { [T!'[" NS!'name_type" T!']" ] }
    'enum_decl": { [T!'enum" N!'ident" T!'[" NS!'ident" T!']"] }
    'statement": { [T!'return" N!'expr" ]
                   [N!'ident"  T!'=" N!'expr"]
                   [N!'ident" T!'!" N!'atom"]
                   [T!'if" N!'condition" T!'{" NS!'statement" T!'}" NO!'else"]
                 }
    'else":      { [T!'else" T!'{" NO!'statement" T!'}" ] }
    'name_type": { [N!'ident" T!':" N!'type_decl"] }
    'type_decl": { [T!'string"]
                   [T!'int"]
                   [T!'bool"]
                   [T!'enum" N!'ident"]
                   [T!'type" N!'ident"]
                   [T!'set<"   N!'type_decl" T!'>"]
                   [T!'map<"   N!'type_decl" N!'type_decl" T!'>"]
                   [T!'order<" N!'type_decl" T!'>"]
                   [T!'[" NA!'typedecl_comma" N!'type_decl" TO!'," T!']"]
                   [T!'[" N!'type_decl" NS!'type_decl" T!']"]
                 }
    'typedecl_comma": {[ N!'type_decl" T!'," ]}

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

    'condition":    { [N!'expr" T!'<" N!'expr"]
                      [N!'expr" T!'>" N!'expr"]
                      [N!'expr" T!'==" N!'expr"]
                      [N!'expr" T!'!=" N!'expr"]
                    }

    'atom": { [N!'ident"]
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
                    '_" '0" '1" '2" '3" '4" '5" '6" '7" '8" '9"},
                R!'"]
             }
    'number": {[T![chars:{'0", '1", '2", '3", '4", '5", '6", '7", '8", '9",} tag:'num"]
                G!'"
                TA![chars:{'0", '1", '2", '3", '4", '5", '6", '7", '8", '9",} tag:'num"]
                R!'"
              ]}
    'str_lit": { [T!<<'>>, G!'", TAN!{<<">>}, T!<<">>, R!'"]
                 [T!'<<", G!'", NA!'str_lit2",  T!'>>",  R!'"]
               }
    'str_lit2": { [TAN!'>"] [T!'>" TN!'>"] }
    'comma_pair": {[N!'expr"   T!',"]}
    'set":   { [T!'{",  T!'}"]
               [T!'{",  NA!'comma_pair",  N!'expr",  TO!',",  T!'}"]
               [T!'{",  N!'expr",   NS!'expr",   T!'}"]
             }
    'order": { [T!'[",  T!']"]
               [T!'[",  NA!'comma_pair",  N!'expr",  TO!',",  T!']"]
               [T!'[",  N!'expr",   NS!'expr",   T!']"]
             }
    'map":   { [T!'{",  T!':",  T!'}"]
               [T!'{",  NA!'kv_comma",  N!'expr",  T!':",  N!'expr",  TO!',",  T!'}"]
               [T!'{",  N!'kv_pair",  NS!'kv_pair",  T!'}"]
             }
    'record": { [T!'[",  T!':",  T!']"]
                [T!'[",  NA!'iv_comma",  N!'iv_pair",  TO!',",  T!']"]
                [T!'[",  N!'iv_pair",  NS!'iv_pair",  T!']"]
              }
    'kv_pair":  {[N!'expr"   T!':"   N!'expr"]}
    'kv_comma": {[N!'expr"   T!':"   N!'expr"   T!',"]}
    'iv_pair":  {[NO!'ident"   T!':"   N!'expr"]}
    'iv_comma": {[N!'iv_pair"  T!',"]}
}
