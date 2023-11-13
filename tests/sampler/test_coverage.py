import pytest

from bootstrap.interpreter import buildCommon, stage2
from bootstrap.sampler import *

seqChoice = '''
{
    'seq":  {[NS!'either"]}
    'either": { [N!'A"] [N!'B"] }
    'A": {[T!'a"]}
    'B": {[T!'b"]}
}
'''
# NOTE: might not like the choices not in brackets inside either

def setupFixture():
    stage1g, _, stage1 = buildCommon()
    res = next(stage1.execute(seqChoice), None)
    assert res is not None
    grammar = stage2(res)
    s = Sampler(grammar)
    return s

def test_singleFixed(capsys):
    with capsys.disabled():
        s = setupFixture()
        for i in range(10):
            res = s.sample_rule('A',1)
            assert(len(res)==1)
            assert(res[0].string=='a')


def test_singleChoice(capsys):
    with capsys.disabled():
        s = setupFixture()
        chosen = set()
        for i in range(10):
            res = s.sample_rule('either',1)
            assert(len(res)==1)
            assert(res[0].string in ("a","b"))
            chosen.add(res[0].string)
        assert(len(chosen)==2 and 'a' in chosen and 'b' in chosen)


def test_biasSingleChoice(capsys):
    with capsys.disabled():
        s = setupFixture()
        for i in range(10):
            res = s.sample_rule('either',1,bias=[('A',1)])
            assert(len(res)==1)
            assert(res[0].string == 'a')


def test_unbiasedSeqLength(capsys):
    with capsys.disabled():
        s = setupFixture()
        print(s.sample_rule('seq',4))

# bias A seq len
# bias B seq len
# unbiased seq contents
# biased A seq contents
# biased B seq contents