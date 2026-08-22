# Mira Project Memory — Current State

**Status:** Active  
**Current Phase:** Idea Validation  
**Gate Status:** G1 ✓ → G2 ●  
**Purpose:** Mira開発における現在の理解・重要な決定・構造仮説・未解決事項・次の検討地点を保持し、会話・時間・環境を越えて思考と仕事を継続できるようにする。

## 1. Development Method

Mira Architectureは、最上位理論を先に完成させるのではなく、

**Hypothesize → Apply → Challenge → Learn → Refine → Reapply**

によって進化させる。

具体的なUse CaseからBottom-upでEvidenceを積み上げる一方、Top-downではValue IntentとIntended Boundaryを持つ。

両者を照合し、

**Intended Boundary − Validated Scope = Coverage Gap**

として、次に検証すべきUse Caseを判断する。

Evidenceが許す範囲を越えて一般化しない。

## 2. Current Structural Hypothesis

### Basic Model

Miraが世界・仕事・Knowledgeを扱う基本構造候補：

**Object + Purpose + State + Relationship**

- **Object:** 何についてなのか
- **Purpose:** 何のために存在・活動するのか
- **State:** 現在どのような状態なのか
- **Relationship:** 他Objectとどのような意味ある関係を持つのか

Stateの具体的内容はObject/Purposeによって異なる。

Knowledge Objectでは、Evidence Strength / Confidence / Validated Scope等が重要なStateとなる。

Relationshipは単なる接続ではなく、必要に応じてDependency / Evidence / Ownership / Rights / Conditions / Governance等のInteraction Rulesを伴う。

### System Structure

**System Level = Hierarchy**

**Actual composition / interaction = Network**

Case / Functionは具体的Capabilityを担い、ProjectはPurposeに応じて必要なFunctions / CapabilitiesをNetworkから選択・統合するOrchestration Systemとして考える。

Miraは、それらのProject / Functionsをさらに統合・学習・発展させる上位Systemとして位置づける。

### Value Structure

System Levelとは独立してValue Scopeを持つ。

Value PerspectiveはIndividual / Team / Company / Stakeholders / Society / Public / Universe等へ拡張可能。

Object/System LevelとValue Scopeを混同しない。

## 3. Knowledge and Wisdom

Knowledgeは単純に「上位へ昇格」するものではない。

まず、

**どのObject / Purpose / System Levelで意味を持ち、再利用可能なのか**

によって配置する。

Knowledgeの動きとして、

- **Stay:** 同じLevelで改善
- **Propagate:** 同Levelまたは他Objectへ再利用
- **Generalize:** より上位・広範なPatternへ抽象化
- **Specialize:** 上位Principleを具体Contextへ適用

を仮説として持つ。

個別結論が前提/Inputによって変化する場合、その結論はVariableである可能性が高い。

複数Use Caseから、Variable / Dependency / Rule / Invariant Candidate / Boundary Conditionsを発見する。

Wisdomは最初から定義する最上位の正解体系ではない。

Evidenceと多様なUse CaseによってConfidenceとValidated Scopeを拡大しながら形成・更新される英知として扱う。

KuniとWisdomは区別する。

### Opinion / Evidence / Understanding

Humanの回答はTruthとして直接扱わず、まず **Opinion / Claim** として扱う。

- **Opinion / Claim:** 人間が現時点でそう考えている、またはそう記憶している内容
- **Evidence-supported Claim:** Document / Data / Test / concrete experience等のEvidenceが付いたClaim
- **Validated Understanding:** 他Human、Document、Data、実運用等とのCross-validationを通じて一定範囲で支持された理解
- **Generalized Knowledge / Principle Candidate:** 異質なUse Caseや反証機会を通じてValidated ScopeとConfidenceが広がった理解

**Opinion + Evidence ≠ Fact / Truth.** Evidence自体の品質、Context、他Evidenceとの整合性、Boundary Conditionsを検証する。

EvidenceのないOpinionも捨てない。暗黙知や経験に基づくOpinionは、HypothesisやEvidence探索を開始するSignalとして保持する。

新しいEvidenceによりValidated Understandingも Challenged / Revised / Scope-limited / Rejected され得る。

## 4. Continuity

MemoryとContinuityを区別する。

Memoryは過去のState、Variable、Evidence等を保持できる。

Continuityは、変化するStateやEnvironmentの中で、Identity / Purpose / Rationale / Relationship / Provenance等の必要な構造的一貫性を維持し、前提・Evidence・Realityの変化に応じて理解・Decision・Stateを再構成できるCapabilityとする。

Private / Company / Public等のBoundaryを情報が越える際には、Disclosure / Access / Ownership / Governanceの評価を必須とする。

## 5. Boundary and Validation

**Intended Boundary:** どこまで成立させたいか。

**Validated Scope:** 現時点のEvidenceで、どこまで成立すると言えるか。

Top-downでIntended Boundaryを設定し、Bottom-upでConcrete Use CasesからValidated Scopeを広げる。

すべてのUse Caseを検討するのではなく、Structural HypothesisをChallengeする情報価値の高いRepresentative / Novel / Edge Casesを選択する。

特に、認知できていないUnknown Unknownが存在することを前提とし、現在のモデルを壊す可能性のあるNovel / Edge Caseを意図的に検討する。

## 6. Idea Formation → Idea Validation → Implementation Planning

従来のIdea Planning → Implementation Planningという二分法を再検討した結果、現時点では以下の3段階をStructural Hypothesisとする。

### Idea Formation

中心問い：

**Can the idea work conceptually?**

成果物：

- Value Intent
- Intended Boundary
- Structural Hypothesis
- Challenge Use Cases
- Evidence Contract
- Known / Known Unknown
- Material risks / falsification conditions

G1は「Ideaが正しい」ことを証明するGateではない。

**Realityで意味ある検証が可能なStructural Hypothesisが成立したか**を判断する。

### Idea Validation

中心問い：

**Does the idea actually work sufficiently in reality, and where does it break?**

Pilot / Prototype / Experiment等によってStructural HypothesisをRealityへ接触させる。

Purposeは、

1. Material Known UnknownをEvidenceによって検証する
2. Unknown Unknownを発見する
3. Structural Hypothesisを修正する
4. Validated Scope / Confidenceを更新する
5. Implementation Planningに必要なUnderstandingを得る

成果物候補：

- Evidence
- Revised Structural Hypothesis
- Validated Scope & Confidence
- Newly discovered Unknowns
- Implementation Implications

G2は「Pilotが成功したか」ではなく、

**Evidenceを通じてIdeaを十分理解し、責任を持ってImplementation Planningを設計できる状態になったか**

を判断する。

### Implementation Planning

中心問い：

**How can the validated idea work reliably, repeatedly and safely in reality?**

Scale / Operations / Ownership / Governance / Resource / Integration / Compliance / Maintenance / Benefit Realization等を設計する。

## 7. Minimum Viable Principle

MVPはIdea Validation固有の概念ではない。

EVT / DVT / PVT等、異なるValidation / Implementation段階に横断的に適用可能な一般原理として扱う。

基本原則：

**次のMaterial Decisionに必要なEvidenceを得るためのMinimum Implementationを行う。**

Minimumとは「可能な限り小さい」ことではなく、

**Material Unknownを検証し、必要なReality Exposureを得られる最小限**

を意味する。

仮説：

**Minimum Build × Maximum Material Learning**

MVP / Minimum Viable Implementationの具体形は、そのPhaseで解決すべきUnknownと必要Evidenceによって変化する。

## 8. Human Evidence Acquisition / Adaptive Discovery

MiraはHumanに複雑なFrameworkを操作させず、Humanが答えやすい具体的な一問一答からEvidenceを獲得する。

基本仮説：

**Human should provide simple, concrete evidence; Mira should bear the complexity of structural integration.**

Humanに「正しいStructure」を直接説明させるのではなく、実際の経験・行動・判断に近い小さなQuestionを用いる。

例：
- このParameterを実際に使う場面はどこですか？
- 最後に使ったとき何を確認しましたか？
- 基準値はどこで確認しますか？
- 変更したら何を再確認しますか？
- 最終的に誰がOKを出しますか？
- そう考える理由や確認できるDocument / Dataはありますか？

Miraは回答をObject / Purpose / State / Relationship / Evidence / Owner / Rule等へ内部的に構造化する。

Human回答は完璧とは仮定しない。本人が確信を示してもOpinion / Claimとして保持し、他Human、Document、Data、実運用等とCross-validationする。

### Adaptive Discovery Loop

**Simple Question → Human Statement → Contextualize → Compare → Detect Agreement / Gap / Contradiction / Unknown → Ask Next Minimum Question → Integrate → Human Confirmation → Repeat as needed**

ContradictionはFailureではなく **high-information discovery trigger** として扱う。

矛盾が見つかった場合、誰かを即座に誤りと判定せず、Hidden Condition / Different Object / Different Purpose / Different Lifecycle State / Local Rule / Outdated Knowledge / Governance Gap等の仮説を立て、追加の簡単なQuestionで解消を試みる。

Question Selection Principle：

**次の一問は、Material Unknownを最も減らしながらHuman Cognitive Costを最小化するものを優先する。**

質問は低認知負荷かつ非誘導的にする。抽象的Framework用語より、具体的経験・行動・直近事例を聞く。

## 9. Current Gate Position

**G1 ✓ — Idea Formation Ready**

Mira Architecture v0.1は、Realityで意味ある検証を行える程度のStructural Hypothesisに到達したと暫定判断。

現在は、

**Idea Validation | G1 ✓ → G2 ●**

へ移行。

G1通過はArchitectureが正しいことを意味せず、検証可能な状態になったことを意味する。

## 10. Current Continuity Pilot

GitHub repositoryをMira Project Memoryのgoverned source-of-truth候補として検証する。

- `PROJECT_MEMORY.md` をCurrent Stateの正本候補とする
- Git historyで過去Stateと変更履歴を保持する
- Apple Notesは当面Human-side working/reference layerとして残す
- Retrieval / context restoration / update effort / change rationale / version history / access & governanceの観点から評価する
- Environmentごとに利用可能なCapability / Permission / Toolが異なり得ることもContinuity上のContextとして扱う

## 11. Pilot A — Master Specification Governance

Master Specification GovernanceをMira Architecture v0.1の最初の実務Validation Use Caseとして使用中。

### Evidence observed

- Object × Purpose Matrixだけでは、Ownership / Evidence / Lifecycle impact / Change Control status等を十分にGovernできなかった
- 実務上StateとRelationshipが必要になったことは、Object + Purpose + State + Relationship仮説を支持するEvidence
- System LevelにはHierarchyがある一方、Parameterは複数Purpose / Lifecycle Event / Verification / Owner等と横断的に関係するためNetworkが必要
- Master MatrixのPurposeはProduct Verification / Process / Supplier / Release / SAP / Quality System / Market / Regulatory等へ拡張中
- Purpose proliferationにより、Purpose / Evidence / System Destination / Governance等が同じPurpose軸に混在していないかをChallengeする必要が出ている
- Matrixを完成させること自体ではなく、実務上答えるべきQuestionに答えられるかをValidation Test Setとして利用できる

### Current architecture assessment

- **U1 Basic Model:** Supported within Master Specification Governance;第五のUniversal Elementを必須とするEvidenceは現時点で未確認
- **U2 Hierarchy × Network:** Partially supported
- **U3 Knowledge Movement:** Generalizationの実例が発生しておりsupported direction
- **U4 Human Usability:** Human Evidence Acquisition / Adaptive DiscoveryとしてPilotを継続

### Next Master Spec validation

Human担当者にMatrix全体やFrameworkを直接レビューさせるのではなく、一つのParameter / Objectについて少数の簡単なAdaptive Questionsを行う。

回答をOpinion / Evidence / Evidence-supported Claimとして保持し、他Role / Document / Dataと照合する。矛盾をDiscovery Triggerとして次のQuestionを生成し、MiraがObject + Purpose + State + Relationship等のLatent Structureを再構築できるか検証する。

## 12. Next Action

**Pilot A — Human Evidence Acquisition / Adaptive Discovery MVPを設計・実施する。**

目的：

1. Humanへの低認知負荷な一問一答から、MiraがMaster Specification GovernanceのLatent Structureを再構築できるか検証する
2. Opinion / Evidence / Validated Understandingの区別が実務で機能するか検証する
3. Contradictionから有益なUnknown / Governance Gapを発見できるか検証する
4. Object + Purpose + State + Relationship仮説をHuman interactionという異なるEvidence SourceでもChallengeする
5. HumanがFrameworkを操作せず、MiraがStructural Complexityを内部で処理できるか評価する

Pilot AのEvidenceを反映した後、Mira Continuity / GitHub等の異質なUse CaseへValidated Scopeを広げる。
