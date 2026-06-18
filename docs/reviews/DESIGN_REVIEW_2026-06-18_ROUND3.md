2026年6月18日付の最新成果物に基づく再レビューです。

## 判定

**`needs-attention` — Round 2の主要指摘はほぼ解消されています。ただし、`SKILL.md` 実装前に直すべきHighが4件残っています。**

二層Schema、base resolution、fail-closed、複数scope component、causal trace、semantic validator、Track A/B eval分離は、きちんと改善されています。OpenAI用Schemaも、静的検査上は「全propertyをrequiredにする」「非対応の`allOf`・`if`・`then`を使わない」「unionにはnested `anyOf`を使う」という現在のStructured Outputs制約に沿っています。([OpenAI Developers][1])

一方、こちらで有効な出力を基に29種類のmutationをvalidatorへ通したところ、**27種類が受理されました**。その中には、明確に拒否すべきscope矛盾、no-op review、secret漏えい、無効digest、参照不整合が含まれています。

---

## 1. High — インストール後、validatorがデフォルト設定で必ず壊れる

`DECISIONS.md` のインストール構成ではSchemaを`assets/`へ配置しています。

```text
unified-adversarial-review/
├── assets/
│   ├── review-output.semantic.schema.json
│   └── review-output.openai.schema.json
└── scripts/
    └── validate_review_output.py
```



しかしvalidatorは、デフォルトで次を探します。

```python
Path(__file__).resolve().parents[1]
/ "schemas"
/ "review-output.semantic.schema.json"
```



実際に`DECISIONS.md`どおりのディレクトリを一時作成して、`--schema`なしで実行したところ、次で停止しました。

```text
FileNotFoundError:
.../schemas/review-output.semantic.schema.json
```

machine modeではvalidatorを必須にしているため、この不一致は実行時blockerです。

### 修正

デフォルトを次へ変更します。

```python
default=(
    Path(__file__).resolve().parents[1]
    / "assets"
    / "review-output.semantic.schema.json"
)
```

さらに、Schemaファイルの不存在、JSON破損、permission errorを捕捉し、tracebackではなく明示的なエラーとexit code `2`を返すべきです。

インストール構成を再現したintegration testも必要です。

```text
test_installed_layout_default_validation
```

---

## 2. High — 何もレビューしていない出力が`approve`相当として通る

現在のsemantic schemaでは、`coverage.checks_performed`はrequiredですが、空配列を許します。

validatorも、findingごとのverificationは確認しますが、review全体の`coverage.checks_performed`が空かどうかは確認していません。`coverage_status=sufficient`について検査しているのは、uncertaintyとlimitationが空かどうかだけです。

そのため、次のような実質no-op出力がvalidになります。

```json
{
  "finding_assessment": "no-material-findings",
  "coverage_status": "sufficient",
  "coverage": {
    "lenses_considered": [],
    "lenses_applied": [],
    "lenses_skipped_with_reason": [],
    "checks_performed": [],
    "limitations": [],
    "sensitive_artifacts": []
  }
}
```

この組み合わせは、core contract上では唯一のpass条件です。

つまり、**対象をほぼ検査していなくてもmachine consumerがapproveできる**状態です。

### 修正

最低限、次を強制します。

```text
coverage.checks_performed minItems: 1

lenses_considered
  = lenses_applied
  ∪ lenses_skipped_with_reason

lenses_applied
  ∩ lenses_skipped_with_reason
  = empty

各配列はunique
```

ただし、専門lensが一つも必要ない変更はあり得ます。したがって「必ずlensを一つ適用」ではなく、専門lensとは別にcore workflowの実施記録を持つほうがよいです。

```json
"core_checks": [
  "target-resolved",
  "change-traced",
  "candidate-refutation-performed"
]
```

より厳密には、各included scope componentに対して、何を確認したかを記録します。

```json
"component_coverage": [
  {
    "scope_component": "branch",
    "status": "evaluated",
    "checks_performed": ["diff inspected", "callers traced"]
  }
]
```

---

## 3. High — scope、base、capabilityが相互矛盾しても通る

`DECISIONS.md` は、`git-aware`をbranch/base/merge-base解決能力、`safe-exec`をcommand実行能力として定義しています。また、branch scopeのbase情報と各scope componentを明示する契約です。

しかし、次はすべてvalidatorを通りました。

```text
branch-diffがincluded
+ branch_component_available=false

branch_component_available=true
+ branch-diffがincludedでない

branch-diffがincluded
+ capability_modesにgit-awareがない

command evidenceが存在
+ capability_modesにsafe-execがない

remote_freshness=unknown
+ coverage_status=sufficient
+ stale-remote limitationなし

branch componentがunavailable
+ reasonなし
+ limitationなし
```

validatorのbase検査は`branch_component_available=true`の一方向だけで、scope componentやcapabilityとの整合性を見ていません。

特に、`remote_freshness=unknown`の場合はcoverage limitationを記録すると明文化されているのに、現在は`sufficient`として通ります。

### 修正

以下をcross-field invariantとして追加します。

```text
included branch-diff
  → branch_component_available=true
  → git-aware present
  → base_ref/base_commit_oid/merge_base_oid present

branch_component_available=false
  → no included branch-diff
  → base refs/OIDs are null
  → resolution method is unavailable or not-applicable

remote_freshness in {local-only, unknown}
  + remote-derived base
  → stale-remote limitation required
  → coverage_status cannot be sufficient

status=unavailable
  → non-empty reason
  → matching coverage limitation

executed command evidence
  → safe-exec present
```

command evidenceが外部から供給されたログである可能性を残すなら、単純に`safe-exec`を要求せず、provenanceを追加します。

```json
"command_origin": "reviewer-executed | host-supplied | user-supplied"
```

`reviewer-executed`の場合だけ`safe-exec`を必須にすればよいです。

---

## 4. High — confidentiality validatorにfalse positiveとfalse negativeが共存している

設計契約は、secret・token・credential・PIIをsummary、evidence、command outputなどへ出さないことを要求しています。

しかし現在のsecret検査は`display_command`だけを対象にし、正規表現も次の少数パターンだけです。

```python
authorization: bearer
--token
api_key
secret
database_url
```



こちらの検査結果では、以下が通りました。

```text
AWS_SECRET_ACCESS_KEY=AKIA...
PASSWORD=abc123
Authorization: Basic ...
ghp_...
summary内のtoken
sensitive_artifact.detail内のpassword
```

一方、正しくredactした次の文字列は拒否されました。

```text
Authorization: Bearer [REDACTED]
```

現在の`\S+`が`[REDACTED]`もsecretとして扱うためです。実際の検査箇所も`display_command`一か所だけです。

path検査にも抜けがあります。現在はUnix/Windowsの絶対pathだけを拒否するため、次が通ります。

```text
../outside/secret.py
```

さらに、`scope.components[].paths`や`intent_sources[].path`はvalidatorのpath検査対象ではありません。

### 修正

まず、secret regexは**安全性の証明ではなくheuristic lint**であると明記すべきです。完全なsecret検出をvalidatorに期待するのは危険です。

そのうえで、

* `[REDACTED]`、`<redacted>`など明示placeholderを許可
* AWS、GitHub、Basic auth、password、client_secret、private-key headerを追加
* summary、detail、evidence、recommendation、excerptなど全ての出力文字列をscan
* `redaction_applied=true`ならredaction noteまたは認識可能なplaceholderを要求
* repository-relative pathは正規化後に`..`、UNC path、`~`、URI形式を拒否
* `scope.paths`、intent path、source path、sensitive artifact pathなど全path fieldを検査

とします。

さらに重要なのは、**host側でtool outputをmodelへ渡す前にredactすること**です。出力後のvalidatorだけでは、すでにmodel contextへ入ったsecretを保護できません。

---

## 5. Medium — SHA-256 digestは現在、証拠ではなく自己申告文字列

`command_evidence`では`digest_algorithm="sha256"`を要求していますが、`command_digest`と`output_digest`は`minLength: 1`だけです。したがって、次もvalidです。

```json
{
  "command_digest": "x",
  "digest_algorithm": "sha256",
  "output_digest": "y"
}
```



64桁hex patternを要求すれば形式上は改善しますが、model自身が生成するdigestをmodel自身の証拠にはできません。元command/outputをvalidatorが受け取らないため、再計算もできません。

### 修正

machine adapterが実行イベントから作るhost-generated evidence manifestへ分離するのがよいです。

```json
{
  "execution_ref": "E-17",
  "command_digest": "...",
  "output_digest": "...",
  "digest_source": "host-computed"
}
```

validatorにはmanifestも渡し、digestを照合します。

portable Skillだけで実行する場合は、

```json
"digest_source": "agent-reported"
```

として、attestationではないことを明示するか、digest fieldそのものを省くほうが誤解がありません。

---

## 6. Medium — semantic schemaとOpenAI schemaで契約内容がずれている

`DECISIONS.md`では、finding、uncertainty、coverage limitation、**next stepのすべて**に`scope_components`を要求しています。

OpenAI schemaでは`next_step.scope_components`がrequiredです。

一方、canonicalなsemantic schemaではrequiredなのは`kind`と`detail`だけで、`scope_components`はoptionalです。

validatorもnext stepのscope参照を検査しないため、

```json
{
  "kind": "fix",
  "detail": "Fix it"
}
```

や、

```json
{
  "kind": "fix",
  "detail": "Fix it",
  "scope_components": ["does-not-exist"]
}
```

が通ります。

同様に、semantic schemaとOpenAI schemaの間には、nullable fieldを必須にするか、省略可能にするかという差が複数あります。これは必ずしも誤りではありませんが、「同じsemantic contract」という説明とは一致しません。

### 修正

`review-output.semantic.schema.json`を唯一のcanonical modelとし、そこからOpenAI subset schemaを生成するのがおすすめです。

少なくともCIで次を検査します。

```text
OpenAI schemaの全fieldがsemantic schemaに存在する
required/nullable変換が定義済み
enumが一致する
semantic-valid outputをnormalizeするとOpenAI-validになる
OpenAI-valid outputはsemantic validatorを通る
```

next step、limitation、component、locationの参照もvalidatorで検査してください。

---

## 7. Medium — evalの「lens別precision/recall」を現在の出力から計算できない

`EVALS.md`は「severityおよびlens別のissue-level precision/recall」を要求しています。

しかしfindingには、どのlensから導かれたかを示すfieldがありません。現在の`type`は、

```text
implementation
design
operability
security
data
compatibility
concurrency
resource
llm-agent
```

となっており、「抽象レベル」と「リスク領域」が混在しています。

そのため、

* design-level security failure
* implementation-level concurrency failure
* operability issue found through data-state lens

を一意に分類できません。

### 修正

次のように分離します。

```json
{
  "finding_level": "implementation | design | operability",
  "risk_domains": [
    "security-trust",
    "data-state",
    "concurrency-distributed"
  ],
  "primary_lens": "concurrency-distributed"
}
```

あるいは、eval gold data側でfinding-to-lens mappingを明示し、reported outputとのmatching ruleを定義します。

---

## 8. Medium — machine modeの外部依存がportability contractに記載されていない

validatorは非標準パッケージ`jsonschema`をimportし、利用できなければmachine validationを完了できません。

しかしcompatibility説明にはGit、command execution、networkしか記載されていません。

Codex Skillsはdeterministic behaviorが必要な場合にscriptsを使うことを推奨していますが、runtime dependencyは配布時に明示する必要があります。([OpenAI Developers][2])

### 修正

次のどれかを選びます。

* Python versionと`jsonschema`の最低versionをcompatibilityに明記
* plugin/adapter側でdependencyをinstall/check
* stdlibだけでcross-field validationし、JSON Schema validationはhostへ委譲
* validatorを単一binaryとして配布

少なくとも、CIで「`jsonschema`なし」「Schemaファイルなし」「破損Schema」の起動失敗をテストしてください。

---

## 解消済みと判断した項目

以下はRound 2の指摘を閉じています。

* OpenAI Structured Outputs用Schemaとsemantic Schemaの分離
* 非対応keywordの除去と全property required化
* same-name branch upstreamをbaseから除外
* fail-closedとcoverage waiverの分離
* finding/uncertaintyの複数scope component対応
* causal traceの構造化
* location IDと`location_ref`
* finding-level verificationの`minItems`
* commandのraw文字列を`display_command`へ変更
* EvalのMethod-only / End-to-end分離
* pushed feature branch tracking caseの追加
* upstream pin、LICENSE、NOTICEの整理

OpenAI用Schemaについては、静的には現在の公式subsetに沿っています。ただし、実際のCodex App Serverで`turn/start.outputSchema`として受理されるend-to-end testは別途必要です。`outputSchema`はcurrent turnにだけ適用されます。([OpenAI Developers][3])

## 実装へ進むための最小修正順

1. validatorの`assets/` path不一致を修正
2. no-op `sufficient`を拒否
3. base・scope・capabilityのcross-field invariantを追加
4. confidentiality検査を「全出力＋全path」へ拡張し、redacted placeholderを許可
5. digestのhost provenanceを定義
6. semantic/OpenAI schema parity testを追加
7. next stepとlimitation ID/referenceを検査
8. dependencyと実App Server integration testを追加

**1〜4を直すまでは`SKILL.md`実装を保留する判断が妥当です。**
そこまで閉じれば、設計契約は実装開始可能な水準にかなり近づきます。

[1]: https://developers.openai.com/api/docs/guides/structured-outputs "Structured model outputs | OpenAI API"
[2]: https://developers.openai.com/codex/skills "Agent Skills – Codex | OpenAI Developers"
[3]: https://developers.openai.com/codex/app-server "App Server – Codex | OpenAI Developers"
