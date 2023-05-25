# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

class Type:
    def __init__(self, label, param1=None, param2=None):
        self.label  = label
        if label=='{}': assert param1 is not None
        if label=='[]': assert param1 is not None
        assert param1 is None or isinstance(param1,Type) or param1=="empty", param1
        self.param1 = param1
        self.param2 = param2

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

    def __eq__(self, other):
        if not isinstance(other,Type):  return False
        return self.label==other.label and self.param1==other.param1 and self.param2==other.param2

    def __hash__(self):
        return hash((self.label, self.param1, self.param2))

    def isFunction(self):
        return self.label=="func"

    def isBuiltin(self):
        return self.label=="builtin"

    def isRecord(self):
        return self.label=='[:]'

    def isSet(self):
        return self.label=='{}'

    def eqOrCoerce(self, other):
        if self==other:                                            return True
        if self.label!=other.label:                                return False
        if self.param2 is None:
            assert other.param2 is None,                           f"{self} ? {other}"
            if self.param1=="empty" or other.param1=="empty":      return True
            return self.param1 is not None and self.param1.eqOrCoerce(other.param1)
        else:
            assert other.param2 is not None,                       f"{self} ? {other}"
            if (self.param1=="empty" or other.param1=="empty") and \
               (self.param2=="empty" or other.param2=="empty"):    return True
            return self.param1 is not None and self.param1.eqOrCoerce(other.param1) and \
                   self.param2 is not None and self.param2.eqOrCoerce(other.param2)

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
