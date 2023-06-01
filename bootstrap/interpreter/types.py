# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

class TypesCannotJoin(Exception):
    pass

class Type:
    def __init__(self, kind, param1=None, param2=None, params=None, zero=None, innerEnv=None, builtin=None):
        self.kind  = kind
        self.param1 = param1
        self.param2 = param2
        self.params = params
        self.innerEnv = innerEnv
        self.builtin = builtin
        self.zero = zero

    def __str__(self):
        if self.kind=="tuple":
            return "[" + " ".join( (":"+str(p) for p in self.params)) + "]"
        if self.kind=="record":
            return "[" + " ".join( (f"{p[0]}:{p[1]}" for p in self.params)) + "]"
        if self.kind=="set":
            return '{' + str(self.param1) + '}'
        if self.kind=="order":
            return '[' + str(self.param1) + ']'
        if self.kind=="map":
            return '{' + f'{self.param1}:{self.param2}' + '}'
        if self.kind=="enum":
            return f'enum [{",".join(self.params)}]'
        if self.kind=="func":
            return f'func {self.param1} -> {self.param2}'
        return self.kind


    def sig(self):
        return (self.kind, self.param1, self.param2, self.params)


    def __eq__(self, other):
        return isinstance(other,Type) and self.sig()==other.sig()


    def __hash__(self):
        return hash(self.sig())


    def isFunction(self):
        return self.kind=="func"  and  self.builtin is None


    def isBuiltin(self):
        return self.kind=="func"  and  self.builtin is not None

    def isRecord(self):
        return self.kind=='record'


    def isSet(self):
        return self.kind=='set'

    def isEnum(self):
        return self.kind=='enum'

    def join(self, other):
        if self.kind=='sum'  and  other.kind=='sum':
            raise TypesCannotJoin(None, f'sum-sum-joins nots implemented')
        if self.kind=='sum'  or   other.kind=='sum':
            if self.kind=='sum':
                sumType, singleType = self, other
            else:
                sumType, singleType = other, self
            for k in sumType.params:
                if k.eqOrCoerce(singleType):
                    return k
            raise TypesCannotJoin(None, f'{singleType} not in {sumType}')

        if self.kind!=other.kind:
            raise TypesCannotJoin(f'{self.kind} and {other.kind} cannot join')

        if self.param1 is not None:
            param1 = self.param1.join(other.param1)
        else:
            param1 = other.param1

        if self.param2 is not None:
            param2 = self.param2.join(other.param2)
        else:
            param2 = other.param2

        if self.kind=="record":
            selfNames, selfTypes  = list(zip(*self.params))
            otherNames, otherTypes = list(zip(*other.params))
            if selfNames!=otherNames:
                raise TypesCannotJoin(f'Records have different labellings: {",".join(selfNames)} and {",".join(otherNames)}')
            joinTypes = (s.join(o) for s,o in zip(selfTypes,otherTypes))
            params = zip(selfNames, joinTypes)
        elif self.kind=="tuple":
            if len(self.params)!=len(other.params):
                raise TypesCannotJoin(f'Anonymous records of different lengths {self}, {other}')
            params = ( s.join(o) for s,o in zip(self.params, other.params) )
        else:
            params = None

        return Type(self.kind, param1=param1, param2=param2, params=params)

    def eqOrCoerce(self, other):
        try:
            combined = self.join(other)
            return True
        except TypesCannotJoin:
            return False
        assert False


    @staticmethod
    def BOOL():
        return Type("bool", zero=False)

    @staticmethod
    def CALL(argType, retType):
        assert isinstance(argType, Type), argType
        assert isinstance(retType, Type), argType
        return Type("call", param1=argType, param2=retType)

    @staticmethod
    def ENUM(myName, names):
        return Type("enum", param1=myName, params=names)

    @staticmethod
    def FUNCTION(argType, retType, innerEnv, builtin=None):
        assert isinstance(argType, Type), argType
        assert isinstance(retType, Type), argType
        assert innerEnv is not None  or  builtin is not None
        return Type("func", param1=argType, param2=retType, innerEnv=innerEnv, builtin=builtin)

    @staticmethod
    def MAP(keyType, valType):
        assert (keyType is None  and  valType is None)  or  \
               (isinstance(keyType, Type)  and  isinstance(valType,Type)), f'{keyType}:{valType}'
        return Type("map", param1=keyType, param2=valType, zero={})

    @staticmethod
    def NUMBER():
        return Type("number",zero=0)

    @staticmethod
    def ORDER(elType):
        assert elType is None  or  isinstance(elType, Type), argType
        return Type("order", param1=elType, zero=[])

    @staticmethod
    def RECORD(pairs):
        empty = {}
        names = set(p[0] for p in pairs)
        assert len(pairs)==len(names), f'Names must be unique within a record'
        for p in pairs:
            assert isinstance(p[1],Type), f'{p[0]} given invalid type: {p[1]}'
            empty[p[0]] = p[1].zero
        return Type("record", params=sorted(pairs), zero=empty)

    @staticmethod
    def SUM(*types):
        for t in types:
            assert isinstance(t,Type)
        return Type("sum", params=tuple(types))

    @staticmethod
    def TUPLE(types):
        vals = []
        for t in types:
            assert isinstance(t,Type), f'{t} is not a valid type in record'
            vals.append(t.zero)
        return Type("tuple", params=tuple(types), zero=tuple(vals))

    @staticmethod
    def SET(elType):
        assert elType is None  or  isinstance(elType, Type), argType
        return Type("set", param1=elType, zero=set())

    @staticmethod
    def STRING():
        return Type("string",zero="")
