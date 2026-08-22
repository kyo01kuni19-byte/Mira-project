# Mira Project Memory — Current State

**Status:** Active  
**Current Phase:** Idea Validation  
**Gate Status:** Mira Architecture G1 ✓ → G2 ● | Pilot A G2-ready candidate ✓ | Pilot B starting  
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

**Logical Structure ≠ Explanation Structure**

Logical StructureはReality / Object / Knowledgeをできるだけ正確に理解・推論・Governするための構造。Object / Purpose / State / Relationship / Evidence / Rule / Dependency / Boundary等の複雑性を必要に応じて保持する。

Connection Functionは、Logical StructureをHumanへそのまま露出させず、**誰に、何のCommunication Purposeで、どのContextにおいて、何をどこまで伝えるか**を判断し、Human-centeredな表現へ変換する。

**Governed Understanding → Human / Communication Purpose / Context → Select / Translate / Project → Human-facing Output**

Explanation StructureはHumanを主人公として構成される。Conversation / Question / Matrix / Presentation / Dashboard / Procedure等はHuman-facing Output / Viewになり得る。

- **Object Purpose:** Objectが何のために存在・利用されるか
- **Communication Purpose:** なぜ今、このHumanにこの情報を伝えるのか

**One governed logical structure can generate multiple human-centered explanation structures through a Connection Function.**

## 4. Discovery Process — Ground before Structure

1. **Object Grounding**
2. **Purpose Grounding**
3. **Human Confirmation**
4. **Context Enrichment** — Internal / Public / Domain Knowledge
5. **Mira Understanding Update**
6. **State / Relationship Hypothesis**
7. **Targeted Evidence Acquisition**
8. **Contradiction / Gap Detection**
9. **Refinement / Validation**

**Object × Purpose anchors understanding.  
Understanding guides evidence acquisition.  
Evidence enables State and Relationship discovery.**

Object × PurposeはSearch Anchor / Search Directionだけでなく、Relationship / Research / Stop ConditionのBoundary Anchorとしても機能する。

## 5. Knowledge / Wisdom / Hypothesis Strength

### Truthを最終Stateとして置かない

**Knowledge is a hypothesis whose support strength and applicable scope evolve with evidence and challenge exposure.**

Human conviction、Mira inference、Document記載のいずれも、それだけでTruthにはしない。

**Opinion / Claim → Hypothesis → Evidence-supported Hypothesis → Validated Understanding → Generalized Principle Candidate → Wisdom Candidate**

これはTruthへの一本道ではなく、新EvidenceによりどのStateからでも **Challenged / Revised / Scope-limited / Rejected** され得る。

### Hypothesis Strength dimensions

- **Evidence Strength** — Evidenceの直接性・品質・再現性
- **Evidence Diversity** — Human / Document / Data / Experiment / Internal Use Case / External Research等の独立性・多様性
- **Challenge Exposure** — Novel / Edge / contradictory cases等への反証Exposure
- **Validated Scope** — どのObject / Purpose / Context / System Levelまで成立確認したか
- **Contradiction Status** — Material contradictionの有無・未解決状態
- **Material Conditions** — 成立/不成立を左右する必要条件・環境条件・依存条件
- **Validated Hierarchy** — どのLearning / System HierarchyでHypothesisが成立しているか

単純な「正しい/間違い」や単一Confidence scoreへ早期に圧縮しない。

## 6. Hierarchical Learning / Generalization Boundary

### Lower-level validityを上位Failureで消さない

HypothesisがあるHierarchy / ScopeでEvidenceにより支持された後、より上位・広範なHierarchyへGeneralizeして成立しなかった場合、**下位でのValidated Learningを自動的に無効化しない**。

例：

**L1 Case → L2 Domain → L3 Governance/System → L4 Mira/Cross-domain → broader Reality**

L4でGeneralizationが失敗しても、L1〜L3で成立したKnowledgeはそのValidated Scopeにおいて保持する。

**Higher-level generalization failure ≠ lower-level knowledge failure.**

上位で成立しなかった事実は、Generalization Boundary / Missing Condition / New Variable / Missing Elementを発見するEvidenceとして保持する。

### Failure type candidate

- **Local Failure:** Hypothesisが元のValidated Scope内でも成立しないEvidenceが出た。元Hypothesis自体をRevise / Rejectする強いSignal
- **Generalization Failure:** 下位Scopeでは成立するが、より上位・異質Scopeでは成立しない。元Knowledgeを削除せず、Boundary / Conditionを更新する
- **Condition Failure:** Hypothesis自体ではなく、成立に必要なMaterial Conditionが欠けていた可能性
- **Execution Failure:** Hypothesis / Conditionは妥当でも、実行方法・Implementationが不十分だった可能性

Failureを一種類として扱わず、**何がFailureしたのか**を分解する。

### Generalization as Challenge

Generalizationは「下位で正しかったKnowledgeを上位へコピーすること」ではない。

**Generalization = 下位でStrengthを得たHypothesisを、より広いHierarchyへChallengeとして投入すること。**

SupportedならValidated Scopeが拡大し、Partially supportedならBoundary Conditionを発見し、成立しなければ上位GeneralizationをRevise / Rejectする。いずれもLearningを生成する。

## 7. Learning Architecture Hypothesis

### Learning definition candidate

**Learning = EvidenceによってHypothesisのStructure・Strength・Scope・Hierarchy・Material Conditions・Relationshipsを更新すること。**

Learningは単なる経験蓄積やConclusionの置換ではない。

基本更新パターン：

**Preserve what still holds → Identify what failed → Discover missing conditions / boundaries → Refine scope / relationship → Update hypothesis → Rechallenge**

### Success and Failure as symmetric evidence

- **Success:** そのContext / Conditions / ScopeでHypothesisを支持するEvidence
- **Failure:** Hypothesis自体、Generalization、Condition、Execution等をChallengeするEvidence

SuccessをUniversal Truthへ無条件Generalizeしない。Failureによって元Knowledgeを無条件削除しない。

人間のLearning Failure候補：
- 成功したCase-level KnowledgeからScope / Conditionsを落とし、上位Hierarchyへ無検証Generalizationする
- 異質ContextでのFailureを、元Scopeで成立していたKnowledgeまで否定するEvidenceとして扱う
- ExperienceからObject / Purpose / Context / Conditions / Evidenceを失い、Conclusionだけを蓄積する
- 矛盾する経験を「どちらが正しいか」で処理し、両方を成立させるHidden Condition / Boundaryを探索しない

MiraはExperienceを **Context + Scope + Hierarchy + Material Conditions + Evidence + Hypothesis + Outcome** と関連づけて保持し、矛盾をKnowledge deletionではなくDifferentiation / Boundary Discoveryへ変換することを目指す。

### Condition-aware success hypothesis

成功確率を上げるとは未来を完全に予測することではなく、

**Hypothesis → Candidate Conditions → Reality Challenge → Outcome × Conditions Learning → Refined Hypothesis**

を反復し、Outcomeを左右するMaterial Conditionsをより正確に理解することと考える。

## 8. Principle / Wisdom

**Principle Candidate = 広いValidated Scope / Hierarchyを持ち、多様なEvidenceで支持され、多くのChallengeを生き残り、Material Conditions / Boundariesが比較的よく理解されている強いHypothesis。**

Wisdomは固定Truthではなく、異なるHierarchy / Scope / ConditionsでのLearningを失わず統合し、Realityの変化に応じて更新可能なUnderstandingとして扱う。

## 9. Evidence Routing and Research Boundary

Material Unknownを見つけても、すぐHumanへ質問または無制限なWeb Researchをしない。

1. Mira Current Knowledge
2. Internal Source
3. Public / External Knowledge
4. Company-specific / tacit / unresolvedならHumanへMinimum Question
5. Contradictionなら追加EvidenceへRouting

### Research Depth

- **Level 1:** Domain Grounding
- **Level 2:** Governance / System Model
- **Level 3:** Parameter / Component — 必要範囲のみ
- **Level 4:** Detailed Technical Mechanism / Optimization — Material Unknownに必要な場合のみ

**Minimum Research × Maximum Structural Learning**

## 10. Human Evidence Acquisition / Adaptive Discovery

**Human should provide simple, concrete evidence; Mira should bear the complexity of structural integration.**

Contradictionは **high-information discovery trigger**。

**Infer freely, commit conservatively.**

Question SelectionはMaterial Unknown / Structural Novelty / Expected Information Gain / Human Cognitive Costを考慮する。

## 11. Idea Formation → Idea Validation → Implementation Planning

G1はTruth判定ではなく、Realityで意味あるValidationが可能なStructural Hypothesisが成立したことを示す。

### G2 as Decision Threshold

**G2 = Implementation Planningへ進むDecisionを正当化できるだけのHypothesis Strengthを得たか。**

100% certaintyを待たず、Remaining uncertainty / contradiction / boundary / conditionsを理解した上で、次PhaseでRealityへ触れるLearning Valueが高くなった地点で進む。

## 12. Pilot A — Master Specification Governance

**Validated Scope:** Master Specification / HTP Consumable Product Lifecycle Governance context  
**Gate:** G2-ready candidate ✓

Pilot AでH1/H2を中心にHuman / Matrix / practical use cases / edge cases / HTP domain grounding / Enterprise Specification・PLM・QMS benchmark等のEvidenceが蓄積。

- **H1 Object + Purpose + State + Relationship:** Strongly supported within Pilot A scope; cross-domain generalization pending
- **H2 Ground Object/Purpose before deeper structuring:** Strongly supported direction within Pilot A; broader validation pending
- **H3 Logical Structure → Connection Function → Explanation Structure:** Strong structural hypothesis; Master Spec外のChallenge Exposureはまだ限定的

Pilot Aの追加Ideationより、異質DomainへのGeneralization ChallengeのInformation Valueが高いと判断。

## 13. Mira Architecture Gate

**Mira Architecture v0.1 = G1 ✓ → G2 ●**

Material Unknown：
- H1/H2/H3が異質DomainでもどこまでTransferするか
- どのHierarchyで成立し、どこでGeneralization Boundaryが現れるか
- Material Conditionsを保持するLearning modelが実際にLearning qualityを改善するか
- Hypothesis Strength / Hierarchical Validity modelがDecision qualityを改善するか

## 14. Pilot B — Mira Continuity / Project Memory / GitHub

**Status:** Starting

Pilot BはMaster Specとは異質な **Knowledge / Memory / Conversation / Environment / Provenance / Access / Continuity** domainを使う。

目的はH1/H2/H3を証明することではなく、Pilot AでStrengthを得たHypothesesを一段上・異質なHierarchyへGeneralization Challengeとして投入し、**何がTransferし、何がTransferせず、どのCondition / Boundaryが必要か**を発見すること。

Pilot Bでは特にLearning Architecture自体をChallengeする。

初期検証軸：
1. Continuity domainのObject / PurposeをGroundできるか
2. H1 Object + Purpose + State + RelationshipでContinuityを十分表現できるか
3. H2 Ground-before-StructureがこのDomainでもResearch / Human Costを改善するか
4. H3 Logical Structure / Connection Function / Explanation StructureがContinuityでも成立するか
5. Project Memory / Git history / Conversation / Environment differencesをContext / State / Relationship / Evidenceとして保持できるか
6. 過去LearningをScope / Hierarchy / Conditionsを失わず継承し、新Evidenceで適切に更新できるか
7. Pilot AからのGeneralization Failureが起きた場合、Pilot A Knowledgeを消さずBoundary Learningとして保存できるか

**Next:** Pilot BのObject / Purpose Groundingから開始する。
