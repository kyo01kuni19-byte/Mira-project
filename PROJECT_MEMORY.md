# Mira Project Memory — Current State

**Status:** Active  
**Current Phase:** Idea Validation  
**Gate Status:** Mira Architecture G1 ✓ → G2 ● | Pilot A G2-ready candidate ✓ | Pilot B active  
**Last Updated:** 2026-08-22  
**Purpose:** Mira開発における現在の理解・重要な決定・構造仮説・Evidence・未解決事項・次の検討地点を保持し、会話・時間・環境を越えて思考と仕事を継続できるようにする。

## 1. Development Method

Mira Architectureは最上位理論を先に完成させず、**Hypothesize → Apply → Challenge → Learn → Refine → Reapply** によって進化させる。

Top-downではValue IntentとIntended Boundaryを持ち、Bottom-upではConcrete Use CaseからEvidenceを積み上げる。

**Intended Boundary − Validated Scope = Coverage Gap**

Evidenceが許す範囲を越えて一般化しない。Representative / Novel / Edge Caseを選び、HypothesisをChallengeする。

ただし、Uncertaintyが存在するだけで専用Validationを作らない。ValidationはDecision / Learning ValueとCostを比較して設計する。

## 2. Current Structural Hypothesis

**Object + Purpose + State + Relationship**

- Object: 何についてなのか
- Purpose: 何のために存在・活動するのか
- State: 現在どのような状態なのか。KnowledgeではHypothesis Strength / Evidence / Validated Scope等も含む
- Relationship: Dependency / Evidence / Ownership / Rights / Conditions / Governance / Composition / Impact / Mechanism / Rationale等を必要に応じて表す

現時点で第五のUniversal Elementを必須とするEvidenceは確認されていない。

**System Level = Hierarchy**  
**Actual composition / interaction = Network**

System Levelとは独立してValue Scopeを持ち、Object/System LevelとValue Scopeを混同しない。

## 3. Logical Structure, Connection Function, Explanation Structure

**Logical Structure ≠ Explanation Structure**

Logical StructureはReality / Object / Knowledgeを正確に理解・推論・Governするための構造。

Connection Functionは、**誰に、何のCommunication Purposeで、どのContextにおいて、何をどこまで伝えるか**を判断しHuman-centeredな表現へ変換する。

**Governed Understanding → Human / Communication Purpose / Context → Select / Translate / Project → Human-facing Output**

Explanation StructureはHumanを主人公として構成され、Conversation / Question / Matrix / Presentation / Dashboard / Procedure / Phase / Gate等になり得る。

- Object Purpose ≠ Communication Purpose
- One governed logical structure can generate multiple human-centered explanation structures through a Connection Function.

## 4. Discovery Process — Ground before Structure

**Object Grounding → Purpose Grounding → Human Confirmation → Context Enrichment → Mira Understanding Update → State/Relationship Hypothesis → Targeted Evidence Acquisition → Contradiction/Gap Detection → Refinement/Validation**

**Object × Purpose anchors understanding. Understanding guides evidence acquisition. Evidence enables State and Relationship discovery.**

Object × PurposeはSearch / Relationship / Research / Stop ConditionのBoundary Anchorとしても機能する。

## 5. Knowledge / Hypothesis Strength

### Truthを最終Stateとして置かない

**Knowledge is a hypothesis whose support strength and applicable scope evolve with evidence and challenge exposure.**

**Opinion / Claim → Hypothesis → Evidence-supported Hypothesis → Validated Understanding → Generalized Principle Candidate → Wisdom Candidate**

新EvidenceによりどのStateからでも Challenged / Revised / Scope-limited / Rejected され得る。

### Hypothesis Strength dimensions

- Evidence Strength
- Evidence Diversity
- Challenge Exposure
- Validated Scope
- Contradiction Status
- Material Conditions
- Validated Hierarchy

単一Confidence scoreや「正しい/間違い」へ早期に圧縮しない。

## 6. Hierarchical Learning / Generalization Boundary

**Higher-level generalization failure ≠ lower-level knowledge failure.**

下位Scopeで成立したHypothesisを上位へGeneralizeして成立しなくても、下位Knowledgeを削除しない。上位FailureはGeneralization Boundary / Missing Condition / New Variable / Missing Elementを発見するEvidence。

Failure type candidate：Local Failure / Generalization Failure / Condition Failure / Execution Failure。

**Generalization = 下位でStrengthを得たHypothesisを、より広いHierarchyへChallengeとして投入すること。**

**Knowledge may move upward before its validity moves upward.**

Mira-level KnowledgeはUniversal Truth置き場ではなく、Cross-project / Cross-domainでChallengeする価値があるHypothesesと、そのEvidence / Scope / Hierarchy / Conditions / Challenge Historyを保持する場所。

## 7. Learning Architecture Hypothesis

**Learning = EvidenceによってHypothesisのStructure・Strength・Scope・Hierarchy・Material Conditions・Relationshipsを更新すること。**

**Preserve what still holds → Identify what failed → Discover missing conditions / boundaries → Refine scope / relationship → Update hypothesis → Rechallenge**

- Success = そのContext / Conditions / ScopeでHypothesisを支持するEvidence
- Failure = Hypothesis / Generalization / Condition / Execution等をChallengeするEvidence

Experienceは **Context + Scope + Hierarchy + Material Conditions + Evidence + Hypothesis + Outcome** と関連づけて保持し、矛盾をKnowledge deletionではなくDifferentiation / Boundary Discoveryへ変換する。

## 8. Validation Strategy Hypothesis

### ValidationはUncertaintyを全部消す活動ではない

Uncertaintyがあること自体は、今すぐValidationする理由にならない。

**Validation Strategy = どのUnknownを、いつ、どのEvidence / Reality Exposureで、どのCostまで払ってValidationする価値があるかを設計・更新すること。**

Validation CostにはHuman Time / Research / Build / Delay / Complexity / Cognitive Load / Opportunity Cost等を含む。

基本判断候補：
- **Low-cost + decision-relevant uncertainty:** 今Validationする
- **High-cost + decision-relevant uncertainty:** まず「今解く必要があるか」を判断。必要ならMinimum Viable Validationを探す
- **Later phaseでEvidence quality / cost / reality exposureが改善する:** Unknown / Options / Risk / Validation Triggerを明示してCarry Forwardする
- **Low-value uncertainty:** 未解決のまま保持する
- **Natural evidence opportunity:** 専用Pilotを作らず、通常実践からEvidenceを取得する

重要な比較：

**Cost / Risk of validating now vs Cost / Risk of carrying uncertainty forward**

### Validation & Validation Planning

Idea Validation PhaseはすべてのValidationを完了するPhaseではない。

**Idea Validation = RealityからLearningしながら、Remaining UnknownをどこでValidationするのが最も合理的かまで設計するPhase。**

Exit Deliverable候補：
- Validated Understanding
- Remaining Material Unknowns
- Open Options
- Conditions / Risks
- Validation Strategy / Timing
- Carry-forward Unknowns
- Next-phase Evidence Requirements / Validation Triggers

**Validation ActivityはPhase横断Capability**であり、Idea Validation / Implementation Planning / EVT / DVT / PVT / Operation等のどこでも起こり得る。

**Minimum Validation Cost × Maximum Material Learning**

## 9. Continuous Learning Loop / Phase-Gate Relationship

### Logical Structure candidate

RealityとのInteractionはPhaseで終了せず、継続的Learning Loopとして捉える。

**Hypothesis → Plan / Apply → Reality Exposure → Observe / Evidence → Validate → Learn → Update → Reapply**

Idea / Pilot / Implementation / OperationのどのContextでもこのLoopは続く。

**Implementation ≠ Completion.**

Implementation後はReality Exposureが増え、Value realization / side effects / changing conditions / operational unknowns / generalization opportunities等の新Evidenceが生まれる。

### Explanation / Governance Structure candidate

Idea Formation → Idea Validation → Implementation Planning → Implementation → Operation等のPhaseは、Continuous Learning RealityをHuman / Organizationが理解・判断・GovernするためのExplanation / Governance Structureとして機能する可能性がある。

したがって、

**Underlying Logical Structure = Continuous Learning Loop**  
**Human-facing / Governance Structure = Phase + Gate**

というH3のcross-domain application candidateを置く。

Phaseを不要とするのではない。Phaseは「現在何を主目的としているか」をHuman / Organizationへ接続する有用なConnection Structure。

## 10. General Gate Architecture Candidate

Gateを特定Phase固有の合否判定ではなく、一般的なTransition Decisionとして仮説化する。

**Gate = Purpose-directed state-transition decision under uncertainty.**

Gate Design candidate：

**Object → Purpose → Current State → Intended Next State → Required Evidence → Material Unknowns → Carry-forward Strategy → Conditions / Risks → Decision Authority → Transition**

Gate Reviewでは、
- What is sufficiently known now?
- What remains unknown?
- Which unknown must be resolved before transition?
- Which can safely move with the Object?
- Where / when will carried uncertainty be validated?
- What is the cost / risk of moving now vs waiting?

を判断する。

**Validation ≠ Gate.**

ValidationはEvidenceを生みState / Hypothesis Strengthを更新する活動。GateはそのState / Evidence / Remaining Uncertaintyを見てTransitionを判断するConnection / Governance Function。

GateはKnowledge completeness testではなく、**Responsible transition decision under uncertainty** と考える。

このGate ModelはIdea / Pilot / Implementation / Release / Learning Generalization / Change Governance等で自然にChallengeし、専用Pilotで証明することを目的化しない。

## 11. Ethical / Normative Governance Hypothesis

**Understanding Reality ≠ Deciding what ought to be done about Reality.**

**Epistemic Strength ≠ Normative Authority.**

- Epistemic Authority
- Governance Authority
- Normative Authority

を分離する。

HumanはTruth Authorityではない。一方、Human / Societyへ重大に作用するNormative DecisionにはHuman Governanceが必要となる可能性が高い。

**Candidate creation ≠ Validation ≠ Normative authorization.**

具体的Boundaryは未検証であり、Ethical Governance Hypothesisとして保持する。

## 12. Principle / Wisdom

**Principle Candidate = 広いValidated Scope / Hierarchyを持ち、多様なEvidenceで支持され、多くのChallengeを生き残り、Material Conditions / Boundariesが比較的よく理解されている強いHypothesis。**

Wisdomは固定Truthではなく、異なるHierarchy / Scope / ConditionsでのLearningを失わず統合し、Realityの変化に応じて更新可能なUnderstanding。

## 13. Evidence Routing / Research Boundary

**Mira Current Knowledge → Internal Source → Public/External Knowledge → Company-specific/tacit Human Evidence → Contradictionなら追加Evidence**

ResearchはStructural HypothesisをChallengeするために必要なDepthまで。

**Minimum Research × Maximum Structural Learning**

## 14. Human Evidence Acquisition / Adaptive Discovery

**Human should provide simple, concrete evidence; Mira should bear the complexity of structural integration.**

Contradictionは high-information discovery trigger。

**Infer freely, commit conservatively.**

## 15. Gate Status

### Pilot A — Master Specification Governance

**Validated Scope:** Master Specification / HTP Consumable Product Lifecycle Governance  
**Gate:** G2-ready candidate ✓

- H1 Object + Purpose + State + Relationship: Strongly supported within Pilot A scope
- H2 Ground Object/Purpose before deeper structuring: Strongly supported direction within Pilot A
- H3 Logical Structure → Connection Function → Explanation Structure: Strong structural hypothesis; Pilot Bでcross-domain evidence増加中

### Mira Architecture v0.1

**G1 ✓ → G2 ●**

Material Unknown：
- H1/H2/H3 cross-domain transferability
- Hierarchical validity / Generalization Boundary
- Learning / Hypothesis Strength modelのDecision value
- Validation Strategy / Gate Architectureのcross-context applicability
- Ethical / Normative Governance Boundary

## 16. Pilot B — Mira Continuity / Project Memory / GitHub

**Status:** Active

### Initial grounding

Continuityさせたいものは単なるStored Memoryではない。

**Mira Level candidate:** Identity / Personality / upper-level values / Learning Architecture / Cross-project Generalized Learning / ability to learn again in new Projects。

**Project Level candidate:** Project Intent / Current Understanding / Hypotheses / Evidence / Decisions / Current State / Next Action / Project-specific Learning。

**Project Memory ≠ Mira Memory.**

Knowledgeは上位へGeneralization Candidateとして移動しても、Validated Scopeは元Projectに留まり得る。

### Continuity Hierarchy challenge

Working Assumptionとして、少なくとも二軸を分けて扱う。

**Knowledge Hierarchy:** KnowledgeがどのScope / Levelで意味を持つか。  
**Continuity Hierarchy:** 何をどの程度失ってはいけないか / 再構築可能でなければならないか。

両軸が独立か強く連動するかを今証明することは目的化しない。Validation ValueがCostを上回るMaterial Decisionが生じた時点で検証する。それまでは二軸をWorking Assumptionとして実務適用し、自然なEvidenceを取得する。

### Cross-domain learning so far

- Candidate creationとValidationは別
- Human Governance AuthorityとEpistemic Strengthは別
- Knowledge placement hierarchyとValidated hierarchyは別
- H3がMaster MatrixだけでなくContinuous Learning Loop vs Phase/Gateにも再出現
- Validation Strategy自体がIdea Validationの重要Capability候補として発生

**Next Reality Challenge:** 現在の `PROJECT_MEMORY.md` を **Knowledge Hierarchy × Continuity Hierarchy** のWorking Assumptionで分類し、現在の1ファイルに異なるContinuity Levelがどう混在しているかを見る。分類結果からRepository / Memory Architectureを決めるのであって、先にStorage Structureを設計しない。
