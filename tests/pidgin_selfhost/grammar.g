{
    'expr": { [N!'atom"]
              [N!'binop1"]
            }
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
    'binop3":     { [N!'binop4",   NA!'binop3_lst"] }
    'binop3_lst": { [T!'@",        N!'binop4"] }
    'binop4":     { [N!'ident",    T!'!",   N!'atom"]
                    [N!'atom"]
                  }
    'atom": { [T!'true"]
              [T!'false"]
              [N!'ident"]
              [N!'number"]
              [N!'str_lit"]
              [N!'set"]
              [N!'map"]
              [N!'order"]
              [T!'(",  N!'expr",  T!')"]
            }
    'ident": { [T!{'A" 'B" 'C" 'D" 'E" 'F" 'G" 'H" 'I" 'J"
                   'K" 'L" 'M" 'N" 'O" 'P" 'Q" 'R" 'S" 'T"
                   'U" 'V" 'W" 'X" 'Y" 'Z"
                   'a" 'b" 'c" 'd" 'e" 'f" 'g" 'h" 'i" 'j"
                   'k" 'l" 'm" 'n" 'o" 'p" 'q" 'r" 's" 't"
                   'u" 'v" 'w" 'x" 'y" 'z"
                   '_"},
                TA!{'A" 'B" 'C" 'D" 'E" 'F" 'G" 'H" 'I" 'J"
                    'K" 'L" 'M" 'N" 'O" 'P" 'Q" 'R" 'S" 'T"
                    'U" 'V" 'W" 'X" 'Y" 'Z"
                    'a" 'b" 'c" 'd" 'e" 'f" 'g" 'h" 'i" 'j"
                    'k" 'l" 'm" 'n" 'o" 'p" 'q" 'r" 's" 't"
                    'u" 'v" 'w" 'x" 'y" 'z"
                    '_" '0", '1", '2", '3", '4", '5", '6", '7", '8", '9"}]
             }
    'number": { [TS!{'0", '1", '2", '3", '4", '5", '6", '7", '8", '9",}] }
    'str_lit": { [T!u('), TAN!{u(")}, T!u(")]
                 [T!'u(", TAN!{')"},  T!')"]
               }
    'set":   { [T!'{",  NA!'elem_lst",  T!'}"] }
    'order": { [T!'[",  NA!'elem_lst",  T!']"] }
    'map":   { [T!'{",  NS!'elem_kv",   T!'}"]
               [T!'{",  T!':",          T!'}"] }

    'elem_kv":  { [N!'expr",  T!':",  N!'expr",  TO!',"] }
    'elem_lst": {[NA!'repeat_elem", N!'final_elem"]}
    'repeat_elem": {[N!'expr", G!'", T!{' " '	" '" ',"}]}
    'final_elem": {[N!'expr", G!'", TO!{' "  '	" '" ',"}]}

}

