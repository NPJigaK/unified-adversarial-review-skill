## 判定

**needs-attention — 現状のまま `SKILL.md` 実装へ進むのは止めたほうがよいです。**

方向性は合っていますが、レビュー精度を左右する中核契約にまだ矛盾があります。今回は `DECISIONS.md` を正本として、`RESEARCH.md`、`HISTORY.md`、`UPSTREAM.md`、`LICENSE`、`NOTICE` との整合性を確認しました。まだ実際の `SKILL.md`、JSON Schema、lens群、eval corpusはないため、これは**実装レビューではなく設計レビュー**です。`RESEARCH.md` 自身も歴史的調査資料であり、現在の決定は `DECISIONS.md` にあると明記しています。

---

## 1. High — 検証で否定された候補を `uncertainty` に残す仕様になっている

**対象:** `DECISIONS.md:368–381`、`HISTORY.md:67–81`

Verifyでは各候補を積極的に反証するとしながら、「このphaseをsurviveできない候補はuncertaintyに属する」と書かれています。これは状態遷移として誤りです。

検証に失敗した候補には、少なくとも二種類あります。

* 既存guardなどによって**反証された候補**
* 必要な証拠がなく、成立・不成立を**判定できなかった候補**

前者は破棄すべきです。uncertaintyへ出すと、実際には否定済みの二重課金、権限漏れ、raceなどが「未解決リスク」として最終出力へ復活します。これは同じ文書の「speculative concernsを報告しない」というfinding barを壊します。

状態を明確に三分してください。

```text
supported
  → final finding

unresolved
  → uncertainty
  条件: materialになり得る具体的経路があり、
        特定の不足証拠によって検証だけが止まっている

refuted / immaterial / out-of-scope / duplicate
  → discard
  最終出力には含めない
```

現在の文言は、誤検知を減らすために追加したVerify phaseが、逆に誤検知の保存装置になる設計です。

---

## 2. High — `assessment` がfinding有無とレビュー完全性を一つのenumに押し込んでいる

**対象:** `DECISIONS.md:149–165`、`402–452`

現在は次の三択です。

```text
material-findings
no-material-findings
insufficient-evidence
```

しかし、現実には次が同時に成立します。

> High findingを1件確認した。
> ただしmigration artifactが読めず、残りのレビューには重大なcoverage gapがある。

この場合、`material-findings` を選ぶと証拠不足が隠れ、`insufficient-evidence` を選ぶと確認済みfindingが隠れます。同様に、findingはないが一部のcoverageだけ限定的、という状態も表現できません。

finding結果とcoverageを直交させるべきです。

```json
{
  "finding_assessment": "material-findings | no-material-findings",
  "coverage_status": "sufficient | limited | insufficient"
}
```

または現在のassessmentを残すなら、少なくとも次の優先規則が必要です。

* 確認済みfindingが一つでもあれば `material-findings`
* 証拠不足は別の `coverage.status` に記録
* `insufficient-evidence` は、findingの有無自体を信頼して判断できない場合だけ
* user focusを評価できなかった場合は最低でも `coverage.status=insufficient`

機械利用するなら、Schemaでも以下を強制する必要があります。

```text
material-findings    → findings minItems: 1
no-material-findings → findings maxItems: 0
```

---

## 3. High — composite scopeが「取りこぼし」を直す代わりに「混入」を起こす

**対象:** `DECISIONS.md:99–119`、`319–322`

defaultで以下をすべて一括レビューする方針です。

* merge baseからHEADまでのcommit済み変更
* staged
* unstaged
* untracked

元版のworking-tree-only問題は確かに直せます。しかし、branchの仕事とローカルの別作業を一つの変更として扱うため、逆方向の事故が起きます。

例えば、branchには認証修正、working treeには無関係な実験コードがあるとします。実験コードのfindingをbranch変更のship blockerとして報告したり、その逆が起こり得ます。現在の `change_relation` には、どのscope componentに関係するfindingかを表すフィールドがありません。

scopeを次のように分解してください。

```text
branch-diff
index-overlay
worktree-overlay
untracked-candidates
```

各componentにIDを付け、findingにも必ず `scope_component` を持たせます。

untrackedについては、全内容を自動で読むべきではありません。まず名前と種別だけ列挙し、変更意図や参照関係から対象であると判断できるものだけ内容を読むべきです。明らかに別作業なら除外し、coverageではなく**意図的除外**として記録します。

また、`change_relation: exposed` は曖昧すぎます。「レビュー中に発見した」だけの既存欠陥を正当化できます。少なくとも以下のdelta evidenceを要求してください。

* 新しい到達経路を作った
* 対象ユーザーやtenantを拡大した
* guardを削除・弱体化した
* 発生確率または影響を上げた
* 外部contractを変更して既存欠陥を到達可能にした

---

## 4. High — base branchの決定方法がnormative specificationに存在しない

**対象:** `DECISIONS.md:317–324`、`477–479`

「merge baseからHEADをレビューする」と決めていますが、**何とのmerge baseか**が未定義です。

候補には次があります。

* 明示されたbase
* branchのupstream
* `origin/HEAD`
* `main`
* `master`
* `trunk`
* ローカルだけに存在するbase
* staleなremote-tracking ref

異なるagentが異なるbaseを選べば、同じrepositoryに対して別のレビュー結果になります。上流実装のbase検出は `RESEARCH.md` に記録されていますが、同文書は非normativeです。

最低限、次を規定してください。

```text
1. user-specified base
2. current branch's configured upstream
3. origin/HEAD
4. configured repository default candidates
5. otherwise branch component unavailable
```

出力にはbase名だけでなく、

```text
base_ref
base_commit_oid
merge_base_oid
base_resolution_method
remote_freshness: verified | local-only | unknown
```

を記録すべきです。

network fetchを勝手に行わず、remote refの鮮度が未確認ならcoverage limitationにします。

---

## 5. High — read-onlyは定義したが、機密性の境界がない

**対象:** `DECISIONS.md:121–139`、`319–333`、`402–452`

repositoryの書き換え禁止とcommandの副作用については改善されています。しかし、**読み取った情報をmodel contextやreview outputへ出す危険**が未処理です。

特にdefault scopeにはuntracked filesが含まれます。そこには次のようなものが入り得ます。

* `.env`
* API token
* private key
* credential fixture
* production dump
* 顧客情報
* incident log
* 個人情報を含むscratch file

read-onlyでも、これらをagentへ読み込ませたり、findingのevidenceに転載すれば漏えいします。Codexではsandboxとnetwork制御は別レイヤーであり、read-onlyだけでデータの扱いが安全になるわけではありません。([OpenAI Developers][1])

Skill本体に次を入れるべきです。

```text
- secret-like filesはmetadataのみ確認し、内容を自動読取しない
- .env、credential、private-key、keystore、production dumpをdefault除外
- secret値、token、key、PIIをbody/evidence/command outputへ転載しない
- findingでは種類と場所のみ示し、値は必ずredact
- command outputにsecretが含まれ得る場合は保存・引用しない
- sensitive artifactを除外した事実をcoverageへ記録
```

これはLLM lensの一項目ではなく、Skillそのものの安全要件です。

---

## 6. High — Output Modelはまだ実装可能なcontractになっていない

**対象:** `DECISIONS.md:402–465`

現在のJSONはschemaではなく概念例です。特に次の問題があります。

### `locations` が一つのobjectで異なる証拠型を扱っている

`kind` には以下があります。

```text
source
config
test
contract
command
missing-control
```

しかし同じobjectには `path`、`line_start`、`line_end` が置かれています。一方、直後のルールではmissing controlやsystem-level contractにはlineを要求しないとしています。内部矛盾です。

`oneOf` を使うべきです。

```text
source_location
  path, line_start, line_end

command_evidence
  command, exit_code, output_digest, relevant_excerpt

missing_control
  expected_anchor, searched_scope, search_method, supporting_paths
```

特に「missing control」は、単に「見つからなかった」だけでは証拠になりません。どこを、何で、どこまで探したかを必須にしないと、設計findingを捏造する抜け道になります。

### 配列のitem shapeが未定義

以下はすべて型が曖昧です。

* `scope.included`
* `scope.excluded`
* `intent_sources`
* `evidence`
* `assumptions`
* `checks_performed`
* `limitations`
* `next_steps`

さらにrequired/optional、空配列許可、重複処理もありません。

### versionがない

adapterとmachine consumerを作るなら最低でも必要です。

```json
{
  "schema_version": "1.0",
  "method_version": "1.0"
}
```

OpenAIのapp-serverでは `outputSchema` は現在のturnだけに適用されます。Skill invocation自体にはschema保証が自動的に付くわけではないため、adapterが正確なschemaを渡せることが重要です。([OpenAI Developers][2])

---

## 7. High — materialityとseverityを使うのに、その定義がない

**対象:** `DECISIONS.md:323–324`、`383–395`、`417–438`

Frameでは「Skillのdefault materiality policyを使う」としています。しかし、そのpolicy自体がnormative文書にありません。

同様にfinal findingのseverityは、

```text
critical
high
medium
```

ですが、判定基準がありません。これではagentごとに、

* データ消失をcriticalにするかhighにするか
* 一部ユーザーのrollback failureをhighにするかmediumにするか
* 検出困難性をseverityへ含めるか
* 発生確率をseverityへ混ぜるか

が変わります。

評価計画はseverity別precision/recallを測るとしていますが、gold severityの基準がなければ指標自体が成立しません。

`finding-calibration.md` に先送りするだけでなく、DECISIONSで最低限の意味を固定してください。

```text
Severity:
  findingが成立した場合の影響

Confidence:
  現在の証拠からfindingが成立する確からしさ

Materiality:
  このSkillの最終出力に載せる最低基準
```

severityには少なくとも以下を使います。

* blast radius
* data/security impact
* reversibility
* user visibility
* recovery cost
* compatibility impact
* operational detectability

発生確率や証拠の弱さはconfidence側へ寄せ、severityを下げる材料にしないほうが安定します。

---

## 8. High — 上流をpinするcommitが文書間で食い違っている

**対象:** `UPSTREAM.md`、`DECISIONS.md:493–505`

`UPSTREAM.md` は、調査snapshotとして次を指定しています。

```text
807e03ac9d5aa23bc395fdec8c3767500a86b3cf
```

さらに、promptはinitial commit後に、

```text
bc8fa661...
fix: avoid embedding large adversarial review diffs
```

で変更されたと記録しています。

しかし `DECISIONS.md` の「Upstream Sources To Pin」は、prompt introduction commitの

```text
c69527eb...
```

をpin対象として挙げています。

これを実装者が正本として読むと、後続のlarge-diff修正を含まないinitial promptをbaseにする可能性があります。

次のどちらか一つへ統一してください。

```text
base_repository_commit: 807e03a...
base_prompt_blob: 78668af...
base_prompt_sha256: 6D3277...
```

`c69527...` と `bc8fa...` は「history」にのみ置きます。pin対象ではありません。

また、CIにhash verificationを置き、`UPSTREAM.md` のhashとvendored/reference contentが一致するか確認したほうがよいです。

---

## 9. Medium — numeric confidenceが、排除したはずのfalse precisionを再導入している

**対象:** `DECISIONS.md:167–187`、`462–463`

evidence-level enumは「単純な強度順ではないためfalse precision」として削除しています。これは妥当です。

ところがconfidenceは0〜1の数値として残し、「calibrated ranking signal」としています。しかし、

* 何についての確率なのか
* 0.8と0.6の意味
* agent間で比較可能か
* model update後も比較可能か
* どのevalでcalibrateするか

が未定義です。

上流互換性はadapterの責務なので、canonical coreにnumeric confidenceを残す理由としては弱いです。

選択肢は二つです。

```text
A. coreでは high / medium / low confidence
   adapterで数値へ変換

B. 数値を維持
   「findingが有効である主観確率」と明確に定義し、
   ECE/Brier scoreなどでmodel・version別に校正
```

校正しない数値なら、カテゴリより精密に見えるだけです。

---

## 10. Medium — 「portable」を主張するための能力contractがない

**対象:** `DECISIONS.md:18–35`、`279–313`

Agent Skills形式がportableでも、実行能力がportableとは限りません。このSkillは事実上、次の能力を期待しています。

* repository file access
* Git diff/history/merge-base
* caller/test/config探索
* optional command execution
* optional primary-source documentation access
* structured output

他のAgent Skills clientがこれを備える保証はありません。Agent Skills仕様には環境要件を表す `compatibility` fieldがあり、tool preapprovalについてはagent実装ごとに対応が異なると明記されています。([Agent Skills][3])

Skillには抽象的なcapability modeを定義してください。

```text
supplied-context mode
  与えられたdiff/contextのみレビュー

repository-read mode
  周辺ファイルを追跡可能

git-aware mode
  merge baseやbranch diffを収集可能

safe-exec mode
  認可・隔離されたcommand検証が可能
```

能力がない場合は黙って簡易レビューせず、coverageへ落とします。

`SKILL.md` frontmatterにも、少なくとも次のような記述が必要です。

```yaml
compatibility: >
  Requires access to the supplied review target.
  Git is required for automatic branch and working-tree scope resolution.
  Command execution and network access are optional.
```

Codex固有の `agents/openai.yaml` はUI metadata、invocation policy、dependency宣言用の任意ファイルなので、portable methodそのものの代替にはなりません。([OpenAI Developers][4])

---

## 11. Medium — lens routingが非normativeなので、agentごとにcoverageが変わる

**対象:** `DECISIONS.md:279–350`

lensファイルは列挙されていますが、「どの変更でどれを読むか」がnormative workflowにありません。「applicable lensesを使う」だけでは、agentによって次が起きます。

* 全lensをロードして浅いチェックリストレビューになる
* security lensだけ過剰適用する
* migrationやoperability lensを読み忘れる
* LLM変更なのにLLM lensが発火しない

最低限のtrigger matrixをnormativeにしてください。

```text
auth / permission / tenant / external input
  → security-trust

write / delete / billing / migration / backfill
  → data-state

async / retry / queue / cache / lock / event
  → concurrency-distributed

schema / API / protocol / config / old client
  → compatibility-migration

deploy / rollback / flag / timeout / monitoring
  → resilience-operability

loop / batch / fan-out / memory / disk / quota
  → resource-safety

prompt / RAG / tool call / MCP / agent memory
  → llm-agent
```

出力も `lenses_applied` だけでなく、

```text
lenses_considered
lenses_applied
lenses_skipped_with_reason
```

にするとsilent omissionを検出できます。

---

## 12. Medium — eval計画では「OpenAI版より改善した」と証明できない

**対象:** `DECISIONS.md:210–242`

eval項目自体はかなり改善されています。しかし、比較対象に**元のOpenAI adversarial-review**が明示されていません。

Unified版はmodeling、lens routing、verification、uncertainty、coverageを追加します。これらはrecallを上げるかもしれませんが、promptを長くしてfocusを薄め、false positiveを増やす可能性もあります。元版と比較しなければ「enhanced」は主張できません。

最低限、同一条件で次を比較してください。

```text
A. upstream OpenAI prompt
B. Unified single-agent
C. Unified optional-subagent
D. ordinary non-adversarial review baseline
```

固定する条件：

* 同一model/version
* 同一target snapshot
* 同一tool access
* 同一context
* 同等token/time budget
* 複数回実行
* blind human adjudication

さらに必要です。

* development setとheld-out test setの分離
* 既知incident名やfix commit messageによるhindsight leakage検査
* repeated-run variance
* confidence interval
* v1 acceptance threshold
* regression gate

「metricsを測る」だけでなく、「Unifiedを採用する最低条件」を決めるべきです。

---

## 13. Medium — 文書分離の決定が、現在の文書自身で守られていない

**対象:** `RESEARCH.md`、`HISTORY.md`、`DECISIONS.md`

`RESEARCH.md` は「superseded assumptionsはHISTORYへ分離した」と冒頭で宣言しています。しかし、後半には依然として、

* Historical Review Result To Preserve
* Superseded Intermediate Conclusion
* withdrawn finding

が残っています。`HISTORY.md` にも同内容が複製されています。

さらにnormativeな `DECISIONS.md` は、冒頭に旧researchへの `needs-attention` verdictを置き、その後10件のhistorical findingを収録しています。これは「normative decisionsとhistoryを分ける」という同文書自身の決定と矛盾します。

整理はこうしたほうが安全です。

```text
DECISIONS.md
  現在の決定だけ。過去のfinding説明を削除

RESEARCH.md
  外部ソース分析と根拠だけ

HISTORY.md
  withdrawn/superseded内容だけ

UPSTREAM.md
  provenanceだけ
```

また、公開repositoryなら `E:\github\...` や `C:\Users\devkey\...` のようなローカル絶対pathは削除・匿名化したほうがよいです。

---

## LICENSE / NOTICE

今回確認した範囲では、`LICENSE` と `NOTICE` に新たなblocking issueは見つけませんでした。

* Apache-2.0本文がある
* OpenAIのNOTICEが保持されている
* OpenAI製品・公式endorsementではないことが書かれている

という方向性は妥当です。上流NOTICEにも `Copyright 2026 OpenAI` とApache-2.0のnoticeがあります。([GitHub][5])

ただし、最終的に上流promptから文言をadaptする `SKILL.md` やreferenceファイルには、計画どおり**変更済みである旨のprominent noticeを各該当ファイルへ入れる**必要があります。これは法的助言ではなく、現在のApache-2.0対応方針との整合性の指摘です。

---

## 修正優先順位

実装前に必ず直すべき順番は次です。

1. 候補の `supported / unresolved / rejected` 状態遷移
2. finding結果とcoverage statusの分離
3. scope component、base resolution、untracked処理
4. secret・PIIの読取／出力redaction
5. 実際に検証可能なJSON Schema
6. materiality・severity・confidenceの定義
7. upstream pinの一本化
8. capability modeとlens trigger
9. upstream版を含む比較eval
10. 文書重複とローカルpathの整理

**現状は思想としては強いですが、精度を上げるために追加した `uncertainty`、composite scope、拡張schemaが、新しい誤検知・対象混入・情報漏えい経路を作っています。** ここを塞いでからSkill本文に落とすべきです。

[1]: https://developers.openai.com/codex/agent-approvals-security "Agent approvals & security – Codex | OpenAI Developers"
[2]: https://developers.openai.com/codex/app-server "App Server – Codex | OpenAI Developers"
[3]: https://agentskills.io/specification "Specification - Agent Skills"
[4]: https://developers.openai.com/codex/skills "Agent Skills – Codex | OpenAI Developers"
[5]: https://github.com/openai/codex-plugin-cc/blob/main/NOTICE "codex-plugin-cc/NOTICE at main · openai/codex-plugin-cc · GitHub"
