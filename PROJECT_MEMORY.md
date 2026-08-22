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

## 8. Current Gate Position

**G1 ✓ — Idea Formation Ready**

Mira Architecture v0.1は、Realityで意味ある検証を行える程度のStructural Hypothesisに到達したと暫定判断。

現在は、

**Idea Validation | G1 ✓ → G2 ●**

へ移行。

G1通過はArchitectureが正しいことを意味せず、検証可能な状態になったことを意味する。

## 9. Current Continuity Pilot

GitHub repositoryをMira Project Memoryのgoverned source-of-truth候補として検証する。

- `PROJECT_MEMORY.md` をCurrent Stateの正本候補とする
- Git historyで過去Stateと変更履歴を保持する
- Apple Notesは当面Human-side working/reference layerとして残す
- Retrieval / context restoration / update effort / change rationale / version history / access & governanceの観点から評価する
- Environmentごとに利用可能なCapability / Permission / Toolが異なり得ることもContinuity上のContextとして扱う

## 10. Next Action

Mira Architecture v0.1をIdea Validationへ投入する。

次に設計するもの：

**Mira Architecture v0.1のMaterial Unknownを最も効率よく検証し、Unknown Unknownにも遭遇できるPilot / Challenge Use Cases。**

Pilotでは本格Implementationを先取りせず、次のDecisionに必要なEvidenceを生み出すMinimum Viable Implementationを設計する。

同時に、今回形成した **Idea Formation → Idea Validation → Implementation Planning** という3段階モデル自体もUse Caseとして検証する。
