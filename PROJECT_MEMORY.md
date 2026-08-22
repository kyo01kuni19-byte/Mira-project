# Mira Project Memory — Current State

**Status:** Active  
**Current Phase:** Idea Validation  
**Gate Status:** G1 ✓ → G2 ●  
**Last Updated:** 2026-08-22  
**Purpose:** Mira開発における現在の理解・重要な決定・構造仮説・Evidence・未解決事項・次の検討地点を保持し、会話・時間・環境を越えて思考と仕事を継続できるようにする。

## 1. Development Method

Mira Architectureは最上位理論を先に完成させず、**Hypothesize → Apply → Challenge → Learn → Refine → Reapply** によって進化させる。

Top-downではValue IntentとIntended Boundaryを持ち、Bottom-upではConcrete Use CaseからEvidenceを積み上げる。

**Intended Boundary − Validated Scope = Coverage Gap**

Evidenceが許す範囲を越えて一般化しない。すべてのUse Caseを検討するのではなく、Structural Hypothesisを最も効率的にChallengeできるRepresentative / Novel / Edge Caseを選ぶ。

## 2. Current Structural Hypothesis

### Representation Model

Miraが世界・仕事・Knowledgeを扱う基本構造候補：

**Object + Purpose + State + Relationship**

- **Object:** 何についてなのか
- **Purpose:** 何のために存在・活動するのか
- **State:** 現在どのような状態なのか。KnowledgeではEvidence Strength / Confidence / Validated Scopeも重要
- **Relationship:** 他Objectとどのような意味ある関係を持つのか。Dependency / Evidence / Ownership / Rights / Conditions / Governance / Composition / Impact / Mechanism / Rationale等を必要に応じて表す

現時点で第五のUniversal Elementを必須とするEvidenceは確認されていない。

### System Structure

**System Level = Hierarchy**  
**Actual composition / interaction = Network**

Case / Functionは具体的Capabilityを担い、ProjectはPurposeに応じて必要なFunctions / CapabilitiesをNetworkから選択・統合するOrchestration Systemとして考える。Miraはそれらをさらに統合・学習・発展させる上位Systemとして位置づける。

### Value Structure

System Levelとは独立してValue Scopeを持つ。Individual / Team / Company / Stakeholders / Society / Public / Universe等へ拡張可能。Object/System LevelとValue Scopeを混同しない。

## 3. Logical Structure, Connection Function, Explanation Structure

一般原則候補として、**理論的に世界を理解する構造と、人間へ説明・接続する構造は同一ではない**とする。

**Logical Structure ≠ Explanation Structure**

### Logical Structure

PurposeはReality / Object / Knowledgeをできるだけ正確に理解・推論・Governすること。必要に応じてObject / Purpose / State / Relationship / Evidence / Rule / Dependency / Boundary等の複雑な構造を保持してよい。

主人公は説明を受けるHumanではなく、**理解対象となるReality / Object**。

### Connection Function

Logical StructureをHumanへそのまま露出させず、**誰に、何のCommunication Purposeで、どのContextにおいて、何をどこまで伝える必要があるか**を判断し、Human-centeredな表現へ変換する機能。

**Governed Understanding → Human / Communication Purpose / Context → Select / Translate / Project → Human-facing Output**

Connection Functionは、理論を単純化すること自体が目的ではなく、Humanが現在のContextで理解し、接続し、判断し、行動できる状態を作ることをPurposeとする。

### Explanation Structure

Humanを主人公として構成される。Conversation / Question / Matrix / Presentation / Dashboard / Procedure等は、Underlying Logical Structureから生成されるHuman-facing Output / Viewになり得る。

同じLogical Structureでも、R&D / QA / Management / Newcomer等で必要なExplanation Structureは異なってよい。

重要な区別：

- **Object Purpose:** Objectが何のために存在・利用されるか
- **Communication Purpose:** なぜ今、このHumanにこの情報を伝えるのか

この二つを混同しない。

基本仮説：

**One governed logical structure can generate multiple human-centered explanation structures through a Connection Function.**

Mira内部の知能・構造が高度になることと、Human側の認知負荷が増えることは同義ではない。Framework-driven Discoveryを避け、Structural ComplexityはMira側で処理し、HumanにはPurpose/Contextに適したConnectionを提供する。

## 4. Discovery Process — Ground before Structure

Representation Modelの4要素は横並びに保持するが、**世界を理解するDiscovery Processには順序がある**。

いきなりObject / Purpose / State / Relationshipをすべて埋めない。まず何について何のために話しているのかをGroundし、Mira自身のDomain Understandingを必要十分な水準まで上げてからState / Relationshipを探索する。

### Current Discovery Sequence

1. **Object Grounding** — 何について話しているのかを特定
2. **Purpose Grounding** — なぜ扱うのか、何のValue / Function / Decisionに関係するかを特定
3. **Human Confirmation** — Object / Purposeの理解を簡単に確認
4. **Context Enrichment** — 必要なInternal / Public / Domain Knowledgeを取得
5. **Mira Understanding Update** — Current UnderstandingとMaterial Unknownを更新
6. **State / Relationship Hypothesis** — State、Dependency、Ownership、Evidence、Impact、Governance、Mechanism等の仮説を作る
7. **Targeted Evidence Acquisition** — Material Unknownだけを最適なEvidence SourceへRouting
8. **Contradiction / Gap Detection** — Agreement / Gap / Contradiction / Unknownを検出
9. **Refinement / Validation** — Structure、Confidence、Validated Scopeを更新

基本仮説：

**Object × Purpose anchors understanding.  
Understanding guides evidence acquisition.  
Evidence enables State and Relationship discovery.**

Objectは「何を調べるか」のSearch Anchor、Purposeは「何を知る必要があるか」のSearch Directionとして機能する。

さらに、Object × Purposeは **どのRelationshipを保持するか、どこまでResearchするか、どこで止めるか** のBoundary Anchorとしても機能する。

## 5. Knowledge / Wisdom / Epistemic State

Knowledgeは単純に上位へ昇格するものではなく、意味のあるObject / Purpose / System Levelへ配置する。

Knowledge movement候補：**Stay / Propagate / Generalize / Specialize**。

HumanやWebの回答をTruthとして直接扱わない。

- **Opinion / Claim:** HumanやSourceがそう主張している
- **Evidence-supported Claim:** Document / Data / Test / concrete experience等が付いたClaim
- **Validated Understanding:** 複数Evidence SourceとのCross-validationで一定Scopeにおいて支持された理解
- **Generalized Knowledge / Principle Candidate:** 異質なUse Case / Challengeを通じてConfidenceとValidated Scopeが広がった理解

**Opinion + Evidence ≠ Fact / Truth.** Evidence自体の品質、Context、Boundary、他Evidenceとの整合性を検証する。

EvidenceのないOpinionも捨てない。暗黙知・経験に基づくOpinionはHypothesis / Evidence探索のSignalとして保持する。

新EvidenceによってValidated Understandingも Challenged / Revised / Scope-limited / Rejected され得る。

Wisdomは最初から定義する最上位の正解体系ではなく、Evidenceと多様なUse Caseによって継続的に形成・更新される。

## 6. Evidence Routing and Research Boundary

Material Unknownを見つけても、すぐHumanへ質問または無制限なWeb Researchをしない。

1. MiraのCurrent Knowledgeで回答可能か
2. Internal Source（Matrix / QMS / Standard / Data / Project Memory等）で確認可能か
3. Public / External Knowledge（Web / literature / regulation / patents等）で確認する価値があるか
4. Company-specific / tacit / unresolvedなら、最適なHumanへMinimum Questionを聞く
5. Sourcesが矛盾する場合はContradictionとして追加EvidenceへRouting

Humanは「最後の手段」ではなく、**HumanにしかないKnowledgeへHuman Costを集中させるEvidence Source**として扱う。Public KnowledgeもTruthではなく、一般Domain KnowledgeとCompany-specific Realityを区別する。

### Research Depth Principle

Ideationでは、Research可能だから深掘りするのではなく、**Structural HypothesisをChallengeするために必要なDepthまでResearchする**。

- **Level 1 — Domain Grounding:** 今回のMaster Spec Pilotでは **HTP Consumable Domain Architecture**。Consumable全体のObject / Parameter families / physical structure / Product Performance / Quality / Manufacturing / Verification & Validation / Shelf-life / Regulatory等の一般構造を理解する。Deviceは今回のGoverned Objectではなく、Consumable requirementを理解するために必要な場合のみExternal Relationship / Boundary Conditionとして参照する
- **Level 2 — Governance / System Model:** Enterprise Specification Management / Lifecycle Governance / PLM / QMS / Requirements / Configuration / Change Control / Digital Thread等。現在のArchitectureを外部PracticeでChallengeするため積極的にResearchする価値が高い
- **Level 3 — Parameter / Component:** Menthol、Total stick length、Trimmer disc等。全体Mechanism / Parameter Setを理解する範囲では有用だが、個々を原則深掘りしない
- **Level 4 — Detailed Technical Mechanism / Optimization:** 個別geometry、最適値、詳細工学等。現在のMaterial UnknownやDecisionに必要な場合のみResearch

基本原則：

**Research at the highest level sufficient to understand and challenge the current Object / Purpose. Drill down only when a material unknown cannot otherwise be resolved.**

**Minimum Research × Maximum Structural Learning**

Research Stop Condition：追加Researchが現在のArchitecture / Structural Hypothesis / Material Decisionを変える可能性が低くなったら止める。

Miraは外部情報をすべてMemoryへ複製せず、Current Structural Understanding、Relevant Source / Provenance、Company-specific Difference、Validated / Unvalidated Relationship等を必要な範囲で保持する。

## 7. Human Evidence Acquisition / Adaptive Discovery

基本仮説：

**Human should provide simple, concrete evidence; Mira should bear the complexity of structural integration.**

HumanにFrameworkや正しいStructureを説明させず、具体的経験・行動・直近事例に近い一問一答を使う。

**Simple Question → Human Statement → Contextualize → Compare → Detect Agreement / Gap / Contradiction / Unknown → Ask Next Minimum Question → Integrate → Human Confirmation**

ContradictionはFailureではなく **high-information discovery trigger** として扱う。

質問は低認知負荷・非誘導的にする。Miraは内部では大胆にHypothesisを作ってよいが、Evidence以上に確定しない。

**Infer freely, commit conservatively.**

Question SelectionはMaterial Unknown / Structural Novelty / Expected Information Gain / Human Cognitive Costを考慮する。

また、次の質問が別Object / Purpose / Scopeに属する場合は質問を止める。

**Stop when the next question belongs to another Object / Purpose / Scope.**

## 8. Idea Formation → Idea Validation → Implementation Planning

### Idea Formation
中心問い：**Can the idea work conceptually?**

成果物候補：Value Intent / Intended Boundary / Structural Hypothesis / Challenge Use Cases / Evidence Contract / Known & Known Unknown / material falsification conditions。

G1はIdeaが正しいことではなく、Realityで意味あるValidationが可能なStructural Hypothesisが成立したことを示す。

### Idea Validation
中心問い：**Does the idea actually work sufficiently in reality, and where does it break?**

Pilot / Prototype / ExperimentでKnown Unknownを検証し、Unknown Unknownを発見し、Structural Hypothesis / Validated Scope / Confidenceを更新する。

G2はPilot成功ではなく、**Evidenceを通じてIdeaを十分理解し、Implementation Planningを責任を持って設計できる状態か**を判断する。

### Implementation Planning
中心問い：**How can the validated idea work reliably, repeatedly and safely in reality?**

Scale / Operations / Ownership / Governance / Resource / Integration / Compliance / Maintenance / Benefit Realization等を設計する。

## 9. Minimum Viable Principle

MVPはIdea Validation固有ではなくEVT / DVT / PVT等を横断する一般原理。

**次のMaterial Decisionに必要なEvidenceを得るためのMinimum Implementationを行う。**

Minimumとは可能な限り小さいことではなく、Material Unknownを検証し必要なReality Exposureを得られる最小限。

**Minimum Build × Maximum Material Learning**

Researchにも同じ考えを適用し、**Minimum Research × Maximum Structural Learning** とする。

## 10. Current Continuity Pilot

GitHub repositoryをMira Project Memoryのgoverned source-of-truth候補として検証中。

- `PROJECT_MEMORY.md` をCurrent Stateの正本候補とする
- Git historyで過去State / change rationaleを保持する
- Apple Notesは当面Human-side working/reference layer
- Retrieval / context restoration / update effort / version history / access & governanceを評価
- EnvironmentごとのCapability / Permission / Tool差もContinuity Contextとして扱う

## 11. Pilot A — Master Specification Governance

Master Specification GovernanceをMira Architecture v0.1の最初の実務Validation Use Caseとして使用中。

### Existing structural evidence

- Object × PurposeだけではOwnership / Evidence / Lifecycle impact / Change Control status等を十分にGovernできず、State + Relationshipの必要性が実務から発生
- Parameterは複数Purpose / Lifecycle Event / Verification / Owner等と横断的に関係し、HierarchyだけでなくNetworkが必要
- Purpose proliferationにより、Purpose / Evidence / System Destination / Governance等が同じPurpose軸に混在していないかChallengeが必要
- Matrixの価値はColumn数ではなく、実務上答えるべきQuestionに答えられるかでValidationできる
- RelationshipはChange Impactを伝播させるKnowledgeとして機能し得る
- **Relationship tells us what to assess; Assessment determines whether change is required.**
- Master Matrixは分散したHuman Know-how / Existing Documents / Dataを抽出・検証し、将来Formal QMS Ruleへ変換する中間Governance Objectとして機能する可能性がある

### Master Matrix Boundary

Master MatrixはAsset Traceability Systemではない。

例えば「Product AがMachine Bで作られ、そのMachineにTrimmer Disc Cが装着されている」という実物Instance Traceabilityを管理することが主Purposeではない。

Master Matrixの主Purposeは、**Product Lifecycle Governance上、どのParameter / Requirementを規定・管理し、どのPurposeで使い、変更時に何をAssessmentすべきかを明示すること**。

したがってRelationshipも「存在するから保持する」のではなく、Governance Purposeに必要なものを保持する。

**Relationship scope is purpose-directed.**

Physical ObjectとGoverned Objectは区別が必要な場合がある。物理的にMachine componentであっても、Matrix上でどのGoverned Objectへ配置するかはMatrixのPurposeとClassification Ruleに依存するため、Physical identityだけでObject classificationを確定しない。

### Human-facing Cognitive Map and Logical Network

Master Matrixの重要な役割は、HumanがParameterを見た瞬間に、**何のために使われているか、自分の仕事とどこで関係するか、変更時に何を気にすべきか**を理解するためのCognitive Mapになること。

一方、Underlying Logical Structureでは、Parameter / Requirementを中心に **Objects / Relationships / States / Evidence** のNetworkをしっかり保持する方向を支持する。

成熟したEnterprise Specification / PLM / QMS ArchitectureとのExternal Challengeでも、RequirementをTest / Manufacturing Process / Change / Configuration / Regulatory Assessment / Document / Owner等へlinkするNetwork型の構造が支持された。

ただし、Master Matrixを単に「backend networkの表示画面」と限定しない。より一般的には、MatrixはMaster Specification Contextにおける **Connection Functionから生成されるHuman-facing Explanation Structure / Cognitive Mapの一つ** と位置づける。
