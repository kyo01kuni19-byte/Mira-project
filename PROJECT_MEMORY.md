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

## 3. Discovery Process — Ground before Structure

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

## 4. Knowledge / Wisdom / Epistemic State

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

## 5. Evidence Routing and Research Boundary

Material Unknownを見つけても、すぐHumanへ質問または無制限なWeb Researchをしない。

1. MiraのCurrent Knowledgeで回答可能か
2. Internal Source（Matrix / QMS / Standard / Data / Project Memory等）で確認可能か
3. Public / External Knowledge（Web / literature / regulation / patents等）で確認する価値があるか
4. Company-specific / tacit / unresolvedなら、最適なHumanへMinimum Questionを聞く
5. Sourcesが矛盾する場合はContradictionとして追加EvidenceへRouting

Humanは「最後の手段」ではなく、**HumanにしかないKnowledgeへHuman Costを集中させるEvidence Source**として扱う。Public KnowledgeもTruthではなく、一般Domain KnowledgeとCompany-specific Realityを区別する。

### Research Depth Principle

Ideationでは、Research可能だから深掘りするのではなく、**Structural HypothesisをChallengeするために必要なDepthまでResearchする**。

- **Level 1 — Domain Grounding:** Heated Tobacco Product等、何の世界を扱っているか。積極的に外部Researchする価値が高い
- **Level 2 — Governance / System Model:** Enterprise Specification Management / Lifecycle Governance / PLM / QMS / Requirements / Configuration / Change Control / Digital Thread等。現在のArchitectureを外部PracticeでChallengeするため積極的にResearchする価値が高い
- **Level 3 — Parameter / Component:** Menthol、Total stick length、Trimmer disc等。全体Mechanism / Parameter Setを理解する範囲では有用だが、個々を原則深掘りしない
- **Level 4 — Detailed Technical Mechanism / Optimization:** 個別geometry、最適値、詳細工学等。現在のMaterial UnknownやDecisionに必要な場合のみResearch

基本原則：

**Research at the highest level sufficient to understand and challenge the current Object / Purpose. Drill down only when a material unknown cannot otherwise be resolved.**

**Minimum Research × Maximum Structural Learning**

Research Stop Condition：追加Researchが現在のArchitecture / Structural Hypothesis / Material Decisionを変える可能性が低くなったら止める。

Miraは外部情報をすべてMemoryへ複製せず、Current Structural Understanding、Relevant Source / Provenance、Company-specific Difference、Validated / Unvalidated Relationship等を必要な範囲で保持する。

## 6. Human Evidence Acquisition / Adaptive Discovery

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

## 7. Idea Formation → Idea Validation → Implementation Planning

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

## 8. Minimum Viable Principle

MVPはIdea Validation固有ではなくEVT / DVT / PVT等を横断する一般原理。

**次のMaterial Decisionに必要なEvidenceを得るためのMinimum Implementationを行う。**

Minimumとは可能な限り小さいことではなく、Material Unknownを検証し必要なReality Exposureを得られる最小限。

**Minimum Build × Maximum Material Learning**

Researchにも同じ考えを適用し、**Minimum Research × Maximum Structural Learning** とする。

## 9. Current Continuity Pilot

GitHub repositoryをMira Project Memoryのgoverned source-of-truth候補として検証中。

- `PROJECT_MEMORY.md` をCurrent Stateの正本候補とする
- Git historyで過去State / change rationaleを保持する
- Apple Notesは当面Human-side working/reference layer
- Retrieval / context restoration / update effort / version history / access & governanceを評価
- EnvironmentごとのCapability / Permission / Tool差もContinuity Contextとして扱う

## 10. Pilot A — Master Specification Governance

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

### Run 1 — Menthol / Known-answer Calibration

HumanへFrameworkを説明せず簡単な一問一答を行い、Specification Verification、SAP Target/Tolerance、Process Validation、Cpk、Shelf-life、Product Quality / Validation / Batch Release Standards、Change Governance等のNetworkを再構築できた。

主なLearning：
- Humanの頭の中にあるNetworkをHuman自身にNetworkとして説明させる必要はない
- 同じParameterでもLifecycle ContextによってRule / criterionが異なる
- Expert confidenceとEvidence Strengthは別
- StandardとStandard外Exception / Escalation Pathを区別
- Requester / Owner / Responsible / Approver等のRelationshipを混同しない
- MiraがHuman回答を先回りして補完するFailure Riskがあり、Infer freely / commit conservativelyが必要

### Run 2 — Total stick length / Structural Novelty

MatrixのObject × Parameter Type × Purpose combinationを解析し、Mentholとは異なる `Machine × Configuration` PatternとしてTST-010 Total stick lengthを選定。

Human Evidenceから以下を発見：
- Total stick lengthはtobacco segment / filter segment等の構成に関係し、変更にはMachine configuration / designへの大きな影響があり得る
- Change impactはMachine Object内に閉じず、tobacco weight、chemical / aerosol-related product performance等のProduct Objectへ伝播し得る
- RelationshipにはComposition / Dependency / Impactだけでなく、必要に応じてMechanism / Rationaleを保持する価値がある
- technical mechanismはChange内容で異なり得る一方、Verification / Validationで評価すべき項目はより安定したGovernance Ruleとして存在し得る
- 現時点ではRuleの相当部分がHuman know-how / distributed knowledgeにあり、Master Matrixがそれを明示化しQMSへFormalizeすることを目指している

### Run 3 — Trimmer disc specification / Edge Case

Matrix上でPurpose接続が薄いRare PatternとしてTrimmer disc specificationをChallenge。

Human Groundingから：
- Trimmer discは物理的にはMachine component
- tobacco densityをControlし、smoke generation / product performanceへ影響し得る重要なmachine-related specification
- しかしMaster MatrixはMachine instance / component traceabilityを目的とせず、「このRequirementをGovernすべき」というGovernance definitionを目的とする

Learning