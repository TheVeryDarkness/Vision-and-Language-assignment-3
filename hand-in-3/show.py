from dataclasses import dataclass
from typing import Callable, Literal
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.axes
import math


@dataclass
class Result:
    semantic: list[float | None]
    non_semantic: list[float | None]
    total: list[float | None]
    semantic_by_type: dict[str, list[float | None]]

    @staticmethod
    def default():
        return Result([None] * 11, [None] * 11, [None] * 11, dict())

# problemt -> semantic/non-semantic/total/(by_type -> type) -> train-{}/tes -> rate


full: dict[str, Result] = dict()
quick: dict[str, Result] = dict()


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


configs: list[tuple[dict[str, Result], str, int]] = [
    (full, 'full', 10000), (quick, 'quick', 1000)]
for data, postfix, total in configs:
    experiments = f'experiments-{postfix}'
    results = [f'{experiments}/SCORER+CBR/test_output/captions',
               f'experiments-{postfix}/SCORER+CBR/eval_sents']
    for dir in results:
        with open(f'{dir}/eval_results.txt') as f:
            m = Machine(f.read())

            while not m.ended():
                if m.try_consume('===================='):
                    point: int
                    if m.try_consume('SCORER+CBR_sents_'):
                        number = int(m.consume_until(' '))
                        point = number * 10 // total - 1
                        m.consume(' results===================')
                        m.lstrip()
                    elif m.try_consume('test'):
                        point = 10
                        m.consume(' results===================')
                        m.lstrip()
                    else:
                        assert False, m.remained()

                    while m.try_consume('-------------'):
                        def caption(key: Literal["semantic", "non_semantic", "total"] | tuple[str]):
                            m.lstrip()
                            while m.peek().isalpha():
                                problem = m.consume_until(':')
                                m.consume(': ')
                                rate = float(m.consume_until('\n'))
                                m.lstrip()
                                data.setdefault(
                                    problem, Result.default())
                                if type(key) == str:
                                    getattr(data[problem], key)[point] = rate
                                else:
                                    _key = key[0]
                                    sbt = data[problem].semantic_by_type
                                    sbt.setdefault(_key, [None] * 11)
                                    sbt[_key][point] = rate
                        if m.try_consume('semantic change captions only (BY TYPE)'):
                            m.consume('----------')
                            m.lstrip()
                            while m.try_consume('['):
                                change_type = m.consume_until(']')
                                m.consume(']')
                                m.lstrip()
                                caption((change_type,))
                        elif m.try_consume('semantic change captions only'):
                            m.consume('----------')
                            caption("semantic")
                        elif m.try_consume('non-semantic change captions only'):
                            m.consume('----------')
                            caption("non_semantic")
                        elif m.try_consume('total captions'):
                            m.consume('----------')
                            m.consume('--')
                            caption("total")
                        else:
                            assert False, m.remained()
                elif m.try_consume('=========Results Summary=========='):
                    break
                else:
                    assert False, m.remained()

species = full.keys()
penguin_means = full

X = 11
x = np.arange(X)  # the label locations
width = 1 / (11 + 1)  # the width of the bars
multiplier = 0

ax: matplotlib.axes.Axes
fig, ax = plt.subplots(layout='constrained')

series = [f"{i}" for i in range(10)] + ["test"]
k: Literal["semantic", "non_semantic", "total"] = "total"
for problem, result in full.items():
    values: list[float] = getattr(result, k)
    offset = multiplier
    print(values)
    rects = ax.bar(x / 12 + offset, values, width=1 / 13)
    ax.bar_label(rects, padding=X, labels=series)
    multiplier += 1


# Add some text for labels, title and custom x-axis tick labels, etc.
ax.set_ylabel('Accuracy')
ax.set_title('Full')
ax.set_xticks(np.arange(8) + 0.5, full.keys())
# ax.legend(loc='upper left', ncols=11)

plt.show()
