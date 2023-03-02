{
    'expr": { [N!'atom"]
              [N!'bin_op1"]
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
    'ident": { [T!({'_"}+lower+upper), TA!({'_"}+lower+upper+digits)] }
    'number": { [TS!digits] }
    'str_lit": { [T!u('), TAN!u("), T!u(")]
                 [T!'u(", TAN!')",  T!')"]
               }
    'set":   { [T!'{",  NA!'expr_lst",  T!'}”] }
    'order": { [T!'[",  NA!'expr_lst",  T!']"] }
    'map":   { [T!'{",  NA!'expr_kv",   T!'}"] }
    'expr_lst": { [N!'expr",  TO!',"] }
    'expr_kv":  { [N!'expr",  T':",  N!'expr",  TO!',"] }

}

