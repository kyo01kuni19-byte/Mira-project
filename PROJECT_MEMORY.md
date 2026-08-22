# Mira Project Memory — Current State

**Status:** Active  
**Current Phase:** Idea Validation  
**Gate Status:** Mira Architecture G1 ✓ → G2 ● | Pilot A G2-ready candidate ✓  
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
- **State:** 現在どのような状態なのか。KnowledgeではHypothesis Strength / Evidence / Validated Scope等も重要
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

Connection Functionは、Humanが現在のContextで理解し、接続し、判断し、行動できる状態を作ることをPurposeとする。

### Explanation Structure

Humanを主人公として構成される。Conversation / Question / Matrix / Presentation / Dashboard / Procedure等は、Underlying Logical Structureから生成されるHuman-facing Output / Viewになり得る。

同じLogical Structureでも、R&D / QA / Management / Newcomer等で必要なExplanation Structureは異なってよい。

重要な区別：
- **Object Purpose:** Objectが何のために存在・利用されるか
- **Communication Purpose:** なぜ今、このHumanにこの情報を伝えるのか

基本仮説：

**One governed logical structure can generate multiple human-centered explanation structures through a Connection Function.**

Mira内部の知能・構造が高度になることと、Human側の認知負荷が増えることは同義ではない。

## 4. Discovery Process — Ground before Structure

Representation Modelの4要素は横並びに保持するが、**世界を理解するDiscovery Processには順序がある**。

1. **Object Grounding** — 何について話しているのかを特定
2. **Purpose Grounding** — なぜ扱うのか、何のValue / Function / Decisionに関係するかを特定
3. **Human Confirmation** — Object / Purposeの理解を簡単に確認
4. **Context Enrichment** — 必要なInternal / Public / Domain Knowledgeを取得
5. **Mira Understanding Update** — Current UnderstandingとMaterial Unknownを更新
6. **State / Relationship Hypothesis** — State、Dependency、Ownership、Evidence、Impact、Governance、Mechanism等の仮説を作る
7. **Targeted Evidence Acquisition** — Material Unknownだけを最適なEvidence SourceへRouting
8. **Contradiction / Gap Detection** — Agreement / Gap / Contradiction / Unknownを検出
9. **Refinement / Validation** — Structure、Hypothesis Strength、Validated Scopeを更新

基本仮説：

**Object × Purpose anchors understanding.  
Understanding guides evidence acquisition.  
Evidence enables State and Relationship discovery.**

Object × PurposeはSearch Anchor / Search Directionだけでなく、どのRelationshipを保持するか、どこまでResearchするか、どこで止めるかのBoundary Anchorとしても機能する。

## 5. Knowledge / Wisdom / Hypothesis Strength

### Truthを最終Stateとして置かない

MiraはKnowledgeを **OpinionかTruthかの二値** で扱わない。

Humanが強く確信していること、Miraが合理的だと考えること、Documentに書かれていることも、それだけでTruthにはしない。

基本仮説：

**Knowledge is a hypothesis whose support strength and applicable scope evolve with evidence and challenge exposure.**

OpinionとTruthの間に固定境界を置くのではなく、HypothesisがどのEvidenceによって、どのScopeで、どの程度Challengeを生き残っているかを保持する。

### Epistemic progression candidate

**Opinion / Claim → Hypothesis → Evidence-supported Hypothesis → Validated Understanding → Generalized Principle Candidate → Wisdom Candidate**

これはTruthへ向かう一本道ではない。新しいEvidenceによって、どのStateからでも **Challenged / Revised / Scope-limited / Rejected** され得る。

### Hypothesis Strength dimensions

単一Confidence scoreだけでなく、少なくとも次を分けて考える。

- **Evidence Strength:** Evidence自体の直接性・品質・再現性等
- **Evidence Diversity:** Human / Document / Data / Experiment / Internal Use Case / External Research等、独立したEvidence Sourceの多様性
- **Challenge Exposure:** Novel / Edge / contradictory cases等によってどれだけ反証機会へ曝されたか
- **Validated Scope:** 現時点でどのObject / Purpose / Context / System Levelまで成立を確認したか
- **Contradiction Status:** Material contradictionが存在するか、未解決か、説明可能か

Hypothesis Strengthはこれらの組合せとして扱い、単純な「正しい/間違い」や一つの数値へ早期に圧縮しない。

### Principle / Wisdom

Principleも絶対Truthとは定義しない。

**Principle Candidate = 広いValidated Scopeを持ち、多様なEvidenceで支持され、多くのChallengeを生き残っている比較的強いHypothesis。**

Wisdomも固定された最終Truthではなく、Evidence / Reality / Boundaryの変化に応じて更新可能なUnderstandingとして扱う。

### Current major hypotheses

- **H1:** Object + Purpose + State + Relationship
- **H2:** Ground Object / Purpose before deeper research and State / Relationship structuring
- **H3:** Logical Structure → Connection Function → Explanation Structure

Human convictionはこれらを探索する重要なSignalだが、Hypothesis Strengthとは分離する。Pilot AではH1/H2を中心にHuman / Matrix / practical use cases / edge cases / external enterprise benchmark等のEvidenceが積み上がった。H3はMaster Matrix / Adaptive Discoveryから強いStructural Hypothesisとして生まれたが、Master Spec以外でのChallenge Exposureはまだ限定的。

## 6. Evidence Routing and Research Boundary

Material Unknownを見つけても、すぐHumanへ質問または無制限なWeb Researchをしない。

1. MiraのCurrent Knowledgeで回答可能か
2. Internal Source（Matrix / QMS / Standard / Data / Project Memory等）で確認可能か
3. Public / External Knowledge（Web / literature / regulation / patents等）で確認する価値があるか
4. Company-specific / tacit / unresolvedなら、最適なHumanへMinimum Questionを聞く
5. Sourcesが矛盾する場合はContradictionとして追加EvidenceへRouting

HumanはHumanにしかないKnowledgeへHuman Costを集中させるEvidence Source。Public KnowledgeもTruthではなく、一般Domain KnowledgeとCompany-specific Realityを区別する。

### Research Depth Principle

- **Level 1 — Domain Grounding:** 今回のMaster Spec PilotではHTP Consumable Domain Architecture
- **Level 2 — Governance / System Model:** Enterprise Specification Management / Lifecycle Governance / PLM / QMS / Requirements / Configuration / Change Control等
- **Level 3 — Parameter / Component:** 全体Mechanism / Parameter Set理解には有用だが、個々を原則深掘りしない
- **Level 4 — Detailed Technical Mechanism / Optimization:** Material Unknown / Decisionに必要な場合のみ

**Research at the highest level sufficient to understand and challenge the current Object / Purpose. Drill down only when a material unknown cannot otherwise be resolved.**

**Minimum Research × Maximum Structural Learning**

## 7. Human Evidence Acquisition / Adaptive Discovery

**Human should provide simple, concrete evidence; Mira should bear the complexity of structural integration.**

HumanにFrameworkや正しいStructureを説明させず、具体的経験・行動・直近事例に近い一問一答を使う。

**Simple Question → Human Statement → Contextualize → Compare → Detect Agreement / Gap / Contradiction / Unknown → Ask Next Minimum Question → Integrate → Human Confirmation**

ContradictionはFailureではなく **high-information discovery trigger**。

**Infer freely, commit conservatively.**

Question SelectionはMaterial Unknown / Structural Novelty / Expected Information Gain / Human Cognitive Costを考慮する。

**Stop when the next question belongs to another Object / Purpose / Scope.**

## 8. Idea Formation → Idea Validation → Implementation Planning

### Idea Formation
中心問い：**Can the idea work conceptually?**

G1はIdeaが正しいことではなく、Realityで意味あるValidationが可能なStructural Hypothesisが成立したことを示す。

### Idea Validation
中心問い：**Does the idea actually work sufficiently in reality, and where does it break?**

Known Unknownを検証し、Unknown Unknownを発見し、Structural Hypothesis / Validated Scope / Hypothesis Strengthを更新する。

### G2 as a Decision Threshold

G2はTruth判定ではない。

**G2 = Implementation Planningへ進むDecisionを正当化できるだけのHypothesis Strengthを得たか。**

100% certaintyを待たない。Remaining uncertainty / contradiction / boundaryを理解した上で、Ideationで追加Evidenceを得るInformation Valueより、次PhaseでRealityへ触れるLearning Valueが高くなった地点で進む。

### Implementation Planning
中心問い：**How can the sufficiently validated idea work reliably, repeatedly and safely in reality?**

## 9. Minimum Viable Principle

**次のMaterial Decisionに必要なEvidenceを得るためのMinimum Implementationを行う。**

**Minimum Build × Maximum Material Learning**

Researchにも **Minimum Research × Maximum Structural Learning** を適用する。

## 10. Current Continuity Pilot

GitHub repositoryをMira Project Memoryのgoverned source-of-truth候補として検証中。

- `PROJECT_MEMORY.md` をCurrent Stateの正本候補とする
- Git historyで過去State / change rationaleを保持
- Apple Notesは当面Human-side working/reference layer
- Retrieval / context restoration / update effort / version history / access & governanceを評価
- EnvironmentごとのCapability / Permission / Tool差もContinuity Contextとして扱う

## 11. Pilot A — Master Specification Governance

### Validated Scope

現時点のValidated Scopeは **Master Specification / HTP Consumable Product Lifecycle Governance context**。

### Evidence base

Pilot Aは少なくとも次の異なるEvidence Source / Challengeを経験した。

- Existing Master Matrix / Presentation / internal structural work
- Human adaptive interview: Menthol known-answer calibration
- Structurally novel case: Total stick length
- Edge / boundary case: Trimmer disc specification
- HTP Consumable Level 1 domain grounding
- Enterprise Specification / PLM / QMS / Requirements / Change Control Level 2 external benchmark

### Main supported findings

- Object × PurposeだけではOwnership / Evidence / Lifecycle impact / Change Control等に不足し、State + Relationshipが実務から必要になった
- HierarchyだけでなくNetworkが必要
- RelationshipはChange Impactを伝播させるKnowledgeとして機能し得る
- Master MatrixはAsset TraceabilityではなくProduct Lifecycle Governance上のCognitive / Governance Map
- Purposeはminimal / stableに保ち、Evidence / System Destination / Lifecycle usage / Change等をRelationshipとして分離する方向に内部・外部Evidenceがある
- Underlying Logical StructureではParameter / Requirementを中心にObjects / Relationships / States / EvidenceのNetworkを保持する方向が支持される
- Master MatrixはLogical Structureそのものではなく、Master Specification ContextにおけるHuman-facing Explanation Structure / Cognitive Mapとして位置づけられる
- Humanへのsimple adaptive questionsからcomplex latent structureを再構築できる初期Evidenceがある
- Ground-before-Structure / Evidence Routing / Research Boundaryの有効性をPilot中のscope correction自体から観測した

### Current Pilot A Hypothesis Strength

- **H1 Object + Purpose + State + Relationship:** Strongly supported within Pilot A Validated Scope; diverse internal/human/external evidence; no material contradiction identified; cross-domain generalization not yet validated
- **H2 Ground Object/Purpose before deeper structuring:** Strongly supported direction within Pilot A; several scope/research corrections demonstrated value; broader domain validation pending
- **H3 Logical Structure → Connection Function → Explanation Structure:** Strong structural hypothesis; strongly coherent with Master Matrix / Adaptive Discovery evidence, but challenge exposure outside Master Spec remains limited

### Pilot A Gate

**Pilot A = G2-ready candidate ✓**

これはMaster Specificationが完成した、またはHypothesesがTruthになったことを意味しない。

Pilot Aの追加Ideationを続けるより、異質なDomainへHypothesesを移しChallengeする方がInformation Valueが高いと暫定判断する。

## 12. Mira Architecture Gate

**Mira Architecture v0.1 = G1 ✓ → G2 ●**

Mira全体のG2はまだ通過しない。

Material Unknown：
- H1がMaster Specification以外の異質Domainでも成立するか
- H2のDiscovery Sequenceが異質DomainでもHuman Costを下げつつUnderstandingを改善するか
- H3がMaster Spec以外でもLogical complexityとHuman-facing explanationを適切に分離できるか
- Hypothesis Strength model自体が実際のLearning / Decisionを改善するか

## 13. Next Action — Pilot B

**Pilot B — Mira Continuity / Project Memory / GitHub**

Master Specとは異質なKnowledge / Memory / Conversation / Environment / Provenance / Access domainを使い、H1/H2/H3とHypothesis Strength modelをChallengeする。

Pilot Bでは「仮説が正しいことを証明する」のではなく、Pilot Aで高まったHypothesis Strengthが異質Domainへ移したときにどこまで維持され、どこで弱まり、どこで修正が必要になるかを観察する。

初期Challenge Questions：
1. Continuity domainのObject / Purposeは何か
2. Object/Purpose Groundingを先