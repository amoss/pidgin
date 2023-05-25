# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

from .box import Box
from .types import Type

def builtin_len(arg):
    print(f'Builtin len: {arg}')
    if arg.type.isSet():
        return Box(Type('box num'), len(arg.raw))
    assert False, f'Unimplemented builtin_len on {arg.type}'

