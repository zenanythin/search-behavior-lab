# Search behavior lab: find the input that separates two explanations

A small Python standard-library exercise for planning a reverse-engineering investigation. Compare three search hypotheses on eight synthetic cases, then add observations from a target you are authorized to inspect. The lab never starts REA, opens a target, sends network requests, or infers how a real application is implemented.

Prepared by the maintainer of the [independent Reverse Engineering Anything learning guide](https://reverseengineeringanything.com/), with AI assistance. This is original educational example code, separate from the upstream REA toolkit and its authors. Official REA information is at [morluto/rea](https://github.com/morluto/rea) and [rea.tools](https://rea.tools/).

## Run locally

Requires Python 3.9 or later; no packages to install.

```sh
python3 lab.py
python3 lab.py --self-test
python3 lab.py my-cases.json
```

The first command prints predictions, **not observed application results**. It records the Python and Unicode data versions because normalization behavior belongs to a concrete runtime.

## What the toy implementations predict

| Case | Title / query distinction | Literal substring | Lowercase substring | NFKC + casefold |
| --- | --- | --- | --- | --- |
| control | `alpha notes` / `alpha` | true | true | true |
| case | `Alpha notes` / `alpha` | false | true | true |
| sharp_s | `Straße` / `STRASSE` | false | false | true |
| composed | composed `café` / decomposed `cafe\u0301` | false | false | true |
| fullwidth | fullwidth `ＣＰＵ manual` / `CPU` | false | false | true |
| accent | `café` / `cafe` | false | false | false |
| space | double-space title / single-space query | false | false | false |
| empty | any title / empty query | true | true | true |

These are three **deliberately different models**, not a ranking of correct search algorithms. NFKC compatibility normalization changes distinctions that some products need to preserve. Casefold is not locale-specific collation. None of the models removes accents, tokenizes words, trims spaces, applies permissions, or controls a UI's empty-query behavior.

## Add actual observations without turning unknown into false

Use a JSON array. Each case has a unique `id`, `title`, and `query`. Add `observed` only when you have checked the result. Keep build identity, exact input encoding, starting state and evidence references in your own investigation notes.

```json
[
  {"id": "case-check", "title": "Alpha notes", "query": "alpha", "observed": true},
  {"id": "unicode-next", "title": "Straße", "query": "STRASSE"}
]
```

Here the first synthetic observation leaves both `lower` and `nfkc_casefold` **not falsified**. The second case is unknown and eliminates neither. A useful next check is an input where the remaining models disagree. Do not silently fill in its result using a model's prediction.

If every supplied observation matches a model, that model remains a candidate. It is not proven to be the application's implementation: caching, indexing, locale settings, tokenization and many other models can produce the same small set of outputs. An observation can also contradict all three models; the report returns an empty candidate list instead of inventing a winner.

## Suggested investigation sequence

1. Choose one observable question and an authorized target/build.
2. Capture the title/query bytes and an initial control result.
3. Write at least two possible explanations before collecting more results.
4. Change one feature at a time: case, normalization, width, accent or spaces.
5. Retain the raw observation separately from the interpretation.
6. Use source or runtime evidence to investigate the remaining explanation; report untested boundaries.

See the independent guide for setup navigation, CLI references and official case-study links. This exercise teaches test selection; it makes no claim about REA provider compatibility or the behavior of Notion, a browser, or any other application.

## Validation and limits

Included tests cover discriminating Unicode cases, unknown observations, ambiguous candidates, contradictions and invalid inputs. `--self-test` checks the toy program only. A passing local run does not establish any target application's behavior. The tool reads a user-selected JSON file and writes its report to standard output; keep confidential observations out of public issues and forks.

## License

MIT License. Copyright (c) 2026 Zen Nin.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
