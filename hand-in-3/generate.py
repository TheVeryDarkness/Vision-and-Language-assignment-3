from dataclasses import dataclass
import json
import pathlib


@dataclass
class Item:
    # path: str
    caption: str


@dataclass
class Comparison:
    positive: Item
    negative: Item


if 0:
    prefix = ""
    script = ""
else:
    prefix = "data-"
    script = """
<script defer>
var images = document.getElementsByTagName("img");
function callback(entries) {
    for (let i of entries) {
        if (i.isIntersecting) {
            let img = i.target;
            let trueSrc = img.getAttribute("data-src");
            img.setAttribute("src", trueSrc);
            observer.unobserve(img);
        }
    } 
}
const observer = new IntersectionObserver(callback);
    for (let i of images) {
    observer.observe(i);
}
</script>
"""


def gen(results: list[pathlib.Path], out: pathlib.Path):

    with open(out, 'w') as out:
        for result in results:
            with open(result) as f:
                results = json.load(f)
                compare: dict[str, Comparison] = dict()
                for item in results:
                    caption = item['caption']
                    id: str = item['image_id']
                    if id.endswith('_n'):
                        positive = False
                        id = id.removesuffix('_n')
                        path = f'data/nsc_images/CLEVR_nonsemantic_{id}'
                    else:
                        positive = True
                        path = f'data/sc_images/CLEVR_semantic_{id}'

                    key = id.removesuffix('.png')
                    if key not in compare:
                        compare.setdefault(key, Comparison(None, None))
                    cmp = compare[key]
                    item = Item(caption=caption)
                    if positive:
                        cmp.positive = item
                    else:
                        cmp.negative = item

                out.write('''
<html>
<head></head>
<body>
<h1>Comparison</h1>
<p>Put this to the root of the repository to show.</p>
<style>
div {
    display:flex;
    justify-content: center;
    align-items:center;
}
img, td {
    width: 32vw;
}
</style>
''')

        print(len(compare))

        for id, cmp in sorted(compare.items()):
            assert cmp.positive is not None
            assert cmp.negative is not None

            out.write(f'''
<div>
<table>
<caption>Case {id}</caption>
<tr>
    <td>Original Image</td>
    <td>{cmp.positive.caption}</td>
    <td>{cmp.negative.caption}</td>
</tr>
<tr>
    <td><img {prefix}src="data/images/CLEVR_default_{id}.png" alt="Original" /></td>
    <td><img {prefix}src="data/sc_images/CLEVR_semantic_{id}.png" alt="Positive" /></td>
    <td><img {prefix}src="data/nsc_images/CLEVR_nonsemantic_{id}.png" alt="Negative" /></td>
</tr>
</table>
</div>
''')

        out.write(f'''
</body>
{script}
</html>
''')


if 1:
    postfix = 'full'
    iter = '10000'
else:
    postfix = 'quick'
    iter = '1000'

experiments = pathlib.Path(f'experiments-{postfix}')

assert experiments.is_dir()

# Validation
validation = experiments / f'SCORER+CBR/eval_sents/SCORER+CBR_sents_{iter}/'

if validation.is_dir():
    gen([validation/'total_results.json'],
        pathlib.Path(f'eval-validation-{postfix}.html'))


# Test
test = experiments / f'SCORER+CBR/test_output/captions/test'

if test.is_dir():
    gen([test/'total_results.json'], pathlib.Path(f'eval-test-{postfix}.html'))
