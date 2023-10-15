import pytest

from bootstrap.interpreter import buildCommon, stage2
from sampler import *

def setupFixture():
    stage1g, _, stage1 = buildCommon()
    res = next(stage1.execute( open('bootstrap/interpreter/grammar.g').read()), None)
    if res is None:
        print(f"Failed to parse grammar from {args.grammar}")
        sys.exit(-1)
    grammar = stage2(res)
    s = Sampler(grammar)
    return s

# python3 bootstrap/sampler.py -s 1 -n 1 -r binop1_lst -b if_stmt=0
def test_lst_without_if(capsys):
    with capsys.disabled():
        s = setupFixture()
        print(renderText(s.sample_rule('binop1_lst',4,bias=[('if_stmt',0)])))