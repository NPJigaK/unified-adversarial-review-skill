2026年6月18日付の修正版ドキュメントに基づく再レビューです。

## 判定

**`needs-attention` — 前回の主要指摘は大部分が適切に解消されています。ただし、`SKILL.md` 実装前に直すべきHighが3件残っています。**

特に良くなったのは、候補状態の分離、findingとcoverageの直交化、scope component、機密情報境界、severity/confidence定義、lens routing、upstream pin、比較evalです。前回レビューを表面的に反映したのではなく、設計へきちんと落とし込めています。

一方、今回新たに確認できた問題は以下です。

---

## 1. High — 現在のSchemaはCodex `outputSchema`としてそのまま使えない

**対象:** `review-output.schema.json:61–95, 144–180, 244–351`

今回のSchemaは一般的なJSON Schema Draft 2020-12としては正しいです。こちらでもmeta-schema validationと、`finding_assessment`に応じた`minItems` / `maxItems`の条件を確認できました。

しかし、これは**Codex App Serverの`outputSchema`で強制するSchemaとして適合していることを意味しません**。

現在のSchemaは次を使っています。

* rootの`allOf`
* `if` / `then`
* `locations`の`oneOf`
* 多数のoptional property



OpenAIのStructured OutputsはJSON Schemaのsubsetのみをサポートし、`allOf`、`if`、`then`は明示的に非対応です。また、すべてのpropertyを`required`にする必要があり、optional値は`null`とのunionなどで表現します。対応するunionは`anyOf`で、現在の`oneOf`は対応一覧にありません。未対応Schemaをstrict modeへ渡すとエラーになると公式仕様に明記されています。([OpenAI Developers][1])

Codex App Serverはturnごとに`outputSchema`を受け取りますが、適用はそのturnだけです。公開仕様には、OpenAI Structured Outputsより広いdialectを受理するという保証はありません。([OpenAI Developers][2])

### 影響

Codex adapterで、

```text
review-output.schema.json
→ turn/start.outputSchema
```

とそのまま渡すと、レビュー開始時点でSchema rejectionになる可能性が高いです。

つまり、現状の「Schemaによるmachine-mode enforcement」はまだ成立していません。

### 推奨修正

Schemaを二層化してください。

```text
schemas/
├── review-output.semantic.schema.json
│   # Draft 2020-12。保存済み結果の完全なshape検証用
│
└── review-output.openai.schema.json
    # Codex/OpenAI Structured Outputs subset専用
```

OpenAI用Schemaでは、

* `allOf` / `if` / `then`を使わない
* `oneOf`を、`kind`で排他的になる`anyOf`へ変更
* 全propertyをrequiredにする
* optional値は`null`、空配列、または明示的な`present`状態で表す
* assessmentとfinding件数の関係は後段validatorへ移す

とします。

そして、Codex adapterは必ず`review-output.openai.schema.json`を使い、生成後にsemantic validatorを通す構成がよいです。

---

## 2. High — `current branch configured upstream`はreview baseではない

**対象:** `DECISIONS.md:189–211`

現在のbase resolutionは次の順です。

```text
1. user-specified base
2. current branch configured upstream
3. origin/HEAD
4. main / master / trunk
```



これは一般的なfeature branchで重大な取りこぼしを起こします。

たとえば、

```bash
git push -u origin feature
```

を行うと、feature branchのupstreamは通常`origin/feature`になります。Gitのupstream trackingは、`git pull`元やローカルbranchとremote-tracking branchの関係を示すもので、PRのmerge targetを意味しません。`--track=direct`では開始branchそのものがupstreamになります。([Git][3])

手元でも次を再現しました。

```text
current branch:             feature
configured upstream:       origin/feature
HEAD:                       5b2ab0...
origin/feature:             5b2ab0...
merge-base with upstream:  5b2ab0...
files vs upstream:         空

origin/HEAD:                origin/main
files vs origin/HEAD:      f.txt
```

featureをpush済みなら、`HEAD`と`origin/feature`が同じになるため、

```text
merge-base(HEAD, origin/feature)..HEAD
```

は空です。結果として、**commit済みfeature変更がすべてreview scopeから消えます**。

これは以前直したはずの「branch差分を取りこぼさない」という目的を、別経路で再発させます。

### 推奨するbase resolution

```text
1. user-specified base
2. host-provided PR/MR base
3. repository-specific review base config
4. origin/HEAD
5. configured default candidates: main / master / trunk
6. otherwise unavailable
```

`current branch configured upstream`を使うのは、次を確認できる場合だけにしてください。

* upstreamが現在branchと同名のremote branchではない
* integration targetとして明示設定されている
* HEADとupstream tipが同一でも「変更なし」と誤判定しない

Schemaの`base_resolution_method`も、

```diff
- branch-upstream
+ host-review-base
+ repository-review-base
```

へ寄せたほうが安全です。

EVALSには必ず次のcaseを加えるべきです。

```text
feature branchがorigin/featureをtrackしている
featureはpush済み
origin/HEADはorigin/main
期待結果: branch-diffはmainとのmerge-baseから収集される
```

---

## 3. High — Schema-validでも意味的に破綻した結果を大量に通せる

**対象:** `review-output.schema.json`全体

現在のSchemaに対して、意図的に次の出力を作りました。

* `branch_component_available=true`なのにbase ref/OIDなし
* findingが存在しないscope componentを参照
* `location_ref`が存在しないlocationを参照
* `line_start=10`, `line_end=1`
* verificationの全配列が空
* unresolved uncertaintyがあるのに`coverage_status=sufficient`
* unavailable-base limitationがあるのに`coverage_status=sufficient`
* 同じlensを`applied`と`skipped`の両方に登録

結果は、

```text
Draft202012Validator errors: 0
```

でした。

これはJSON Schemaの限界だけではなく、現在のSchema内の具体的な欠落によります。

### 3.1 `location_ref`の参照先が存在しない

`delta_evidence`と`evidence_item`には`location_ref`があります。

しかし、`source_location`、`command_evidence`、`missing_control`のいずれにもlocation IDがありません。

したがって、現状の`location_ref`は**必ずdangling referenceになり得る、参照不能なfield**です。

各locationへ、

```json
{
  "id": "L-1"
}
```

を追加するか、`location_ref`を削除してください。

### 3.2 findingの因果経路をSchemaが要求していない

設計契約は、

```text
preconditions
→ trigger
→ reachable path
→ failed guard / unsafe transition
→ violated invariant
→ impact
```

を必須としています。

しかしSchemaでは、

* `violated_invariant`はoptional
* `impact`はoptional
* precondition、trigger、failed guardの専用fieldなし
* `body`は1文字でもvalid

です。

`body`へ全部書く運用も可能ですが、machine contractとしては検証不能です。

次のような構造を推奨します。

```json
"causal_trace": {
  "preconditions": ["..."],
  "trigger": "...",
  "reachable_path": ["..."],
  "failed_guard_or_transition": "...",
  "violated_invariant": "...",
  "impact": "..."
}
```

### 3.3 verificationが空でも通る

`checks_performed`と`refutations_checked`はrequiredですが、`minItems`がありません。つまり両方空でもvalidです。

final findingには最低でも、

```text
checks_performed minItems: 1
refutations_checked minItems: 1
```

を要求すべきです。

### 3.4 referential integrityとset関係がない

次は通常のJSON Schemaだけでは十分に保証できません。

* finding/uncertaintyのscope componentが実在する
* 参照先componentが`included`
* component ID、finding ID、location IDが一意
* location_refが実在する
* `line_end >= line_start`
* applied lensがconsidered lensのsubset
* applied lensとskipped lensがdisjoint
* `sufficient`ならmaterialなuncertaintyがない
* available baseならbase ref/OID/merge-baseが存在する

このため、以前の「validator scriptはruntime dependencyにしない」という判断を少し修正すべきです。

> 人間向けMarkdown modeでは不要。
> **machine mode、CI gate、Codex adapterではdeterministic semantic validatorを必須にする。**

CodexのSkill指針も、通常はinstructionsを優先しつつ、deterministic behaviorが必要な場合はscriptを使うよう推奨しています。([OpenAI Developers][4])

また、Git OIDのpattern、

```regex
^[0-9a-fA-F]{40,64}$
```

は41〜63桁も許します。

次にしてください。

```regex
^(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})$
```

---

## 4. High — fail-closed方針と`accepted limited`が矛盾している

**対象:** `DECISIONS.md:423–443`

文書はまず、

> machine consumerは`no-material-findings + sufficient`以外をfail closedする

と定義しています。

しかし直後のOpenAI adapterでは、

```text
no-material-findings + sufficient or accepted limited
→ approve
```

としています。

`accepted limited`について、

* 誰がacceptしたか
* どのlimitationをacceptしたか
* どのpolicyに基づくか
* 有効期限
* machine outputのどこに記録するか

が未定義です。

現Schemaにもcoverage waiverはありません。

### 影響

adapter実装者が単に、

```text
limited → approve
```

と解釈すると、unreadable migration、stale base、sensitive artifact除外などがあるreviewでもapproveを返せます。

### 推奨修正

coreのdefault mappingはこれだけにしてください。

```text
no-material-findings + sufficient
→ approve

それ以外
→ needs-attention
```

限定的coverageを組織policyで許容したい場合は、review resultとは別のpolicy inputにします。

```json
"coverage_waiver": {
  "accepted_limitation_ids": ["C-2"],
  "accepted_by": "...",
  "reason": "...",
  "policy_ref": "...",
  "expires_at": "..."
}
```

これはportable coreではなくhost/release adapterの責務です。

また、`sufficient / limited / insufficient`のうち、現在は`insufficient`の説明はありますが、`sufficient`と`limited`の境界が弱いです。最低限、

```text
sufficient:
  requested scopeにmaterialなunresolved uncertaintyがなく、
  release-relevant componentがすべて評価済み

limited:
  assessmentは利用可能だが、明示された非決定的なgapがある

insufficient:
  finding/no-finding判断自体を信頼できない
```

と固定してください。

---

## 5. Medium — Evalが「method比較」と「end-to-end比較」を混同している

**対象:** `EVALS.md:14–46, 99–121`

EVALSは全systemについて、同じcontextを与えるとしています。

一方、stress caseでは、

* dirty branch composite
* unrelated untracked
* sensitive file
* stale base
* large/binary artifact

など、**context collectionとscope resolutionそのもの**を評価しようとしています。

同じ固定contextを与えるなら、Unified版のcollection改善は測れません。
各systemに自力でcollectさせるなら、入力contextが異なるためreview methodの純粋比較になりません。

### 推奨する二本立て

#### Track A: Method-only

```text
全systemへ同一のfrozen review packetを渡す
比較対象:
- adversarial reasoning
- finding precision/recall
- verification
- calibration
```

#### Track B: End-to-end

```text
同一repository snapshotとtarget intentだけを渡す
各systemが自分でscope/contextを収集する
比較対象:
- target completeness
- scope contamination
- sensitive artifact handling
- context cost
- final finding quality
```

upstream baselineについても、

```text
prompt-only
wrapper + prompt
```

を区別するべきです。

### thresholdも事前固定が必要

現在は、

* materially higher
* statistically meaningful
* chosen gate threshold
* allowed threshold

が未定義です。また、「最初のbaseline後にthresholdをtightenできる」という記述は、held-out結果を見てから基準を調整する余地があります。

少なくとも、

* development setでthresholdを決定
* held-out実行前にfreeze
* minimum case count
* repeat count
* effect size
* confidence interval
* superiority/non-inferiority rule

を明記してください。

`machine-mode schema validity`については、Codex adapterでSchema enforcementを使うなら、選択式thresholdではなく**構文validity 100%**が自然です。semantic validator pass rateは別metricに分けます。

---

## 6. Medium — findingが複数scope componentにまたがれない

**対象:** `review-output.schema.json:247–270, 534–565`

findingとuncertaintyはどちらも単一の`scope_component`しか持てません。

しかしcomposite reviewでは、たとえば、

```text
branch-diff:
  新しいwriter

index-overlay:
  schema migration

worktree-overlay:
  feature flag default
```

の組み合わせで初めてfailureが成立することがあります。

一つだけ選ぶと、scope causalityが不正確になります。

次のどちらかがよいです。

```json
"scope_components": ["branch", "index"]
```

または、

```json
"primary_scope_component": "branch",
"related_scope_components": ["index"]
```

EVALSの`expected scope component`も単数ではなく、許容component setに変更してください。

---

## 7. Medium — command evidenceが機密情報を再漏えいさせる

**対象:** `review-output.schema.json:404–435`

機密性の設計自体はかなり改善されています。secret値をquoteせず、command outputはdigestやredacted excerptにする方針は妥当です。

一方、Schemaは完全な`command`文字列を必須にしています。

commandには以下が含まれ得ます。

```bash
curl -H "Authorization: Bearer ..."
tool --token ...
DATABASE_URL=... test-command
```

outputだけredactしても、commandそのものから漏えいします。

次のように変更してください。

```json
{
  "display_command": "curl -H 'Authorization: [REDACTED]' ...",
  "command_digest": "...",
  "digest_algorithm": "sha256",
  "exit_code": 0,
  "output_digest": "...",
  "relevant_excerpt": "...",
  "redaction_applied": true
}
```

`path`についても、原則repository-relative pathか、`[REDACTED_PATH]`を要求したほうが安全です。

---

# 修正済みと判断できる項目

前回の主要findingのうち、以下は閉じています。

* `supported / unresolved / refuted / immaterial / out-of-scope / duplicate`の分離
* refuted candidateをuncertaintyへ戻さないルール
* finding assessmentとcoverage statusの分離
* scope componentの明示
* untracked fileのmetadata-first処理
* sensitive artifactの扱い
* severityとconfidenceの分離
* lens trigger matrix
* upstream snapshot/hashの一本化
* OpenAI版、Unified単体、subagent版、通常reviewの比較計画
* normative/history/research/provenanceの文書分離



LICENSE / NOTICE / UPSTREAMについても、今回の範囲では新しいblocking issueはありません。

---

# 実装へ進むための最小修正順

1. **base resolutionから通常のbranch upstreamを外す**
2. **OpenAI/Codex Structured Outputs用Schemaを別途作る**
3. **machine mode用semantic validatorを必須化する**
4. `location_ref`とlocation IDを整合させる
5. coverage fail-closedとwaiver policyを分離する
6. Evalをmethod-onlyとend-to-endへ分ける
7. scope componentを複数対応にする
8. command/path redactionをSchemaへ反映する

このうち1〜4を直す前に`SKILL.md`へ進むと、**review methodは正しくても、対象差分が空になる、Codex adapterがSchemaを受理しない、壊れた機械出力をvalidとして通す**という、基盤側の失敗になります。

逆に、ここまで直せば設計段階の大きな不確定要素はかなり減ります。今回の改訂は前回より明確に良く、もう「根本思想を考え直す」段階ではなく、**実行契約を壊れない形へ仕上げる段階**です。

[1]: https://developers.openai.com/api/docs/guides/structured-outputs "Structured model outputs | OpenAI API"
[2]: https://developers.openai.com/codex/app-server "App Server – Codex | OpenAI Developers"
[3]: https://git-scm.com/docs/git-branch "Git - git-branch Documentation"
[4]: https://developers.openai.com/codex/skills "Agent Skills – Codex | OpenAI Developers"
