# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

class TypesCannotJoin(Exception):
    pass

class Type:
    def __init__(self, kind, param1=None, param2=None, params=None):
        self.kind  = kind
        self.param1 = param1
        self.param2 = param2
        self.params = params

    def __str__(self):
        if self.label=='[]':
            return f"[{self.param1}]"
        if self.label=='{}':
            return "{" + str(self.param1) + "}"
        if self.label=='{:}':
            return "{" + f"{self.param1}:{self.param2}" + "}"
        if self.label=='[:]':
            return "record"
        return self.label

    def sig(self):
        return (self.kind, self.param1, self.param2, self.params)

    def __eq__(self, other):
        return isinstance(other,Type) and self.sig()==other.sig()

    def __hash__(self):
        return hash(self.sig())

    def isFunction(self):
        return self.kind=="func"

    def isBuiltin(self):
        return self.kind=="builtin"

    def isRecord(self):
        return self.kind=='[:]'

    def isSet(self):
        return self.kind=='{}'

#    def eqOrCoerce(self, other):
#        if self==other:                                            return True
#        if self.label!=other.label:                                return False
#        if self.param2 is None:
#            assert other.param2 is None,                           f"{self} ? {other}"
#            if self.param1=="empty" or other.param1=="empty":      return True
#            return self.param1 is not None and self.param1.eqOrCoerce(other.param1)
#        else:
#            assert other.param2 is not None,                       f"{self} ? {other}"
#            if (self.param1=="empty" or other.param1=="empty") and \
#               (self.param2=="empty" or other.param2=="empty"):    return True
#            return self.param1 is not None and self.param1.eqOrCoerce(other.param1) and \
#                   self.param2 is not None and self.param2.eqOrCoerce(other.param2)

    def join(self, other):
        if self==other: return self
        param1, param2 = None, None
        if isinstance(self.param1,Type) and isinstance(other.param1,Type):
            param1 = self.param1.join(other.param1)
        elif self.param1 == "empty" and other.param1 is not None:
            param1 = other.param1
        elif self.param1 is not None and other.param1 == "empty":
            param1 = self.param1
        if isinstance(self.param2,Type) and isinstance(other.param2,Type):
            param1 = self.param1.join(other.param1)
        elif self.param2 == "empty" and other.param2 is not None:
            param2 = other.param2
        elif self.param2 is not None and other.param2 == "empty":
            param2 = self.param2
        return Type(self.label, param1, param2)


    def join(self, other):
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

        if self.label=="record":
            selfNames, selfTypes  = list(zip(*self.params))
            otherNames, otherTypes = list(zip(*other.params))
            if selfNames!=otherNames:
                raise TypesCannotJoin(f'Records have different labellings: {",".join(selfNames)} and {",".join(otherNames)}')
            joinTypes = (s.join(o) for s,o in zip(selfType,otherTypes))
            params = zip(selfNames, joinTypes)
        elif self.label=="tuple":
            if len(self.params)!=len(other.params):
                raise TypesCannotJoin('Anonymous records of different lengths {len(self.params)}, {len(other.params)}')
            params = ( s.join(o) for s,o in zip(self.params, other.params) )
        else:
            params = None

        return Type(self.label, param1=param1, param2=param2, params=params)


    @staticmethod
    def CALL(argType, retType):
        assert isinstance(argType, Type), argType
        assert isinstance(retType, Type), argType
        return Type("call", param1=argType, param2=retType)

    @staticmethod
    def MAP(keyType, valType):
        assert isinstance(keyType, Type), argType
        assert isinstance(valType, Type), argType
        return Type("map", param1=keyType, param2=valType)

    @staticmethod
    def NUMBER():
        return Type("number")

    @staticmethod
    def ORDER(elType):
        assert elType is None  or  isinstance(elType, Type), argType
        return Type("order", param1=elType)

    @staticmethod
    def RECORD(pairs):
        names = set(p[0] for p in pairs)
        assert len(pairs)==len(names), f'Names must be unique within a record'
        for p in pairs:
            assert isinstance(p[1],Type), f'{p[0]} given invalid type: {p[1]}'
        return Type("record", params=sorted(pairs))

    @staticmethod
    def TUPLE(types):
        for t in types:
            assert isinstance(t,Type), f'{t} is not a valid type in record'
        return Type("tuple", params=types)

    @staticmethod
    def SET(elType):
        assert elType is None  or  isinstance(elType, Type), argType
        return Type("set", param1=elType)

    @staticmethod
    def STRING():
        return Type("string")
