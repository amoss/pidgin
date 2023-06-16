# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

from .box import Box
from .types import Type

def builtin_len(arg):
    print(f'Builtin len: {arg}')
    if arg.type.isSet() or arg.type.isString() or arg.type.isOrder():
        return Box(Type.NUMBER(), len(arg.raw))
    assert False, f'Unimplemented builtin_len on {arg.type}'

def builtin_print(arg):
    print(f'Builtin print: {arg}')

