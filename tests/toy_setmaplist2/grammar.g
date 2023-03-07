{
    'expr": { [N!'atom"]
              [N!'ident",    T!'!",   N!'atom"]
            }
    'atom": { [N!'ident"]
              [N!'str_lit"]
              [N!'set"]
              [N!'map"]
              [N!'order"]
              [T!'(",  N!'expr",  T!')"]
            }
    'set":   { [T!'{",  NO!'elem_lst",  T!'}"] }
    'order": { [T!'[",  NO!'elem_lst",  T!']"] }
    'map":   { [T!'{",  NS!'elem_kv",   T!'}"]
               [T!'{",  T!':",          T!'}"] }
    'elem_kv":  { [N!'expr",  T!':",  N!'expr",  TO!',"] }
    'elem_lst": {[NA!'repeat_elem", N!'final_elem"]}
    'repeat_elem": {[N!'expr", G!'", T!{' " '	" '" ',"}]}
    'final_elem": {[N!'expr", G!'", TO!{' "  '	" '" ',"}]}
    'str_lit": { [T!u('), G!'", TAN!{u(")}, T!u(")]
                 [T!'u(", G!'", TAN!{')"},  T!')"]
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
}
