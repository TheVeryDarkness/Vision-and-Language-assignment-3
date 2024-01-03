from dataclasses import dataclass
from typing import Callable
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.axes


@dataclass
class Result:
    semantic: dict[str, float]
    non_semantic: dict[str, float]
    total: dict[str, float]
    semantic_by_type: dict[str, dict[str, float]]

    @staticmethod
    def default():
        return Result(dict(), dict(), dict(), dict())


@dataclass
class Comparison:
    full: Result
    quick: Result

    @staticmethod
    def default():
        return Comparison(Result.default(), Result.default())

    def get(self, postfix: str):
        match postfix:
            case 'full':
                return self.full
            case 'quick':
                return self.quick
            case _:
                assert False, postfix


# train-{}/test -> full/quick -> ... -> problem -> rate
data: dict[int, Comparison] = dict()


class Machine:
    def __init__(self, s: str) -> None:
        self.s = s
        self.i = 0

    def try_consume(self, prefix: str):
        if (self.s.startswith(prefix, self.i)):
            self.i += len(prefix)
            return True
        return False

    def consume(self, prefix: str):
        assert self.s.startswith(prefix, self.i), self.remained()
        self.i += len(prefix)
        return self.s[self.i-len(prefix):self.i]

    def consume_until(self, sep: str):
        next = self.s.find(sep, self.i)
        assert next != -1, self.remained()
        res = self.s[self.i:next]
        self.i = next
        return res

    def lstrip(self):
        while self.s[self.i].isspace():
            self.i += 1

    def ended(self):
        return self.i == len(self.s)

    def peek(self):
        return self.s[self.i]

    def remained(self):
        return self.s[self.i:]


configs: list[tuple[str, int]] = [('full', 10000), ('quick', 1000)]
for postfix, total in configs:
    experiments = f'experiments-{postfix}'
    results = [f'{experiments}/SCORER+CBR/test_output/captions',
               f'experiments-{postfix}/SCORER+CBR/eval_sents']
    for dir in results:
        with open(f'{dir}/eval_results.txt') as f:
            m = Machine(f.read())

            while not m.ended():
                if m.try_consume('===================='):
                    if m.try_consume('SCORER+CBR_sents_'):
                        number = int(m.consume_until(' '))
                        point = number * 10 // total
                        m.consume(' results===================')
                        m.lstrip()
                    elif m.try_consume('test'):
                        point = 10
                        m.consume(' results===================')
                        m.lstrip()
                    else:
                        assert False, m.remained()

                    data.setdefault(point, Comparison.default())
                    res = data[point].get(postfix)
                    while m.try_consume('-------------'):
                        def caption(f: Callable[[Result], dict[str, float]]):
                            m.lstrip()
                            while m.peek().isalpha():
                                t = m.consume_until(':')
                                m.consume(': ')
                                r = m.consume_until('\n')
                                m.lstrip()
                                data.setdefault(point, Comparison.default())
                                f(res).setdefault(t, float(r))
                        if m.try_consume('semantic change captions only (BY TYPE)'):
                            m.consume('----------')
                            m.lstrip()
                            while m.try_consume('['):
                                t = m.consume_until(']')
                                m.consume(']')
                                res.semantic_by_type.setdefault(t, dict())
                                caption(lambda res: res.semantic_by_type[t])
                        elif m.try_consume('semantic change captions only'):
                            m.consume('----------')
                            caption(lambda res: res.semantic)
                        elif m.try_consume('non-semantic change captions only'):
                            m.consume('----------')
                            caption(lambda res: res.non_semantic)
                        elif m.try_consume('total captions'):
                            m.consume('----------')
                            m.consume('--')
                            caption(lambda res: res.total)
                        else:
                            assert False, m.remained()
                elif m.try_consume('=========Results Summary=========='):
                    break
                else:
                    assert False, m.remained()

species = data
penguin_means = data

x = np.arange(len(species))  # the label locations
width = 1 / len(species)  # the width of the bars
multiplier = 0

ax: matplotlib.axes.Axes
fig, ax = plt.subplots(layout='constrained')

for k0, v0 in data.items():
    v1 = v0.full
    for k2, v2 in (('semantic', v1.semantic), ('non-semantic', v1.non_semantic), ('total', v1.total)):
        for k3, v3 in v0.full.semantic.items():
            offset = width * multiplier
            rects = ax.bar(k0, v3, width=width)
            ax.bar_label(rects, padding=3)
            multiplier += 1


# Add some text for labels, title and custom x-axis tick labels, etc.
ax.set_ylabel('Length (mm)')
ax.set_title('Penguin attributes by species')
ax.set_xticks(x + width, species)
ax.legend(loc='upper left', ncols=3)

plt.show()
