# Migration Plan: OpenSearch Serverless → Amazon S3 Vectors

**Blueprint:** `genai-marketing-campaigns`
**Branch:** `feat/s3-vectors-migration` (worktree, off `origin/main`)
**Status:** Plan — not yet implemented
**Independent of:** the Nova Canvas → Stability AI PR (`feat/stability-clean`, upstream PR #109). This work forks from `origin/main` and shares no commits with it.

---

## 1. Why

The blueprint's vector store is an **OpenSearch Serverless (AOSS) `VECTORSEARCH` collection**. AOSS bills a minimum OCU floor (≈2 indexing + 2 search OCUs) **even when idle** — on the order of **~$700/month** for a demo that sits unused between customer engagements.

**Amazon S3 Vectors** is purpose-built, pay-per-use vector storage: no provisioned infrastructure, near-zero cost at rest, sub-second queries (as low as ~100 ms for frequent queries). For an idle-most-of-the-time "Art of the Possible" blueprint, this is the right cost profile — and it removes an entire IAM/policy/collection stack.

Trade-off (accepted): S3 Vectors targets **infrequent** query workloads. This blueprint is exactly that. A high-QPS production system would keep AOSS (or export an S3 Vectors snapshot to AOSS — a supported path).

## 2. Compatibility check — everything the app uses maps cleanly

| Concern | Current (AOSS) | S3 Vectors | Fits? |
|---|---|---|---|
| Vector dimension | 1024 (Titan Multimodal `outputEmbeddingLength=1024`) | 1–4096 | ✅ |
| Distance metric | `cosinesimil` (nmslib/hnsw) | `cosine` \| `euclidean` | ✅ `cosine` |
| Filter fields | `node`, `objective` (keyword) | filterable metadata (string/number/bool/list) | ✅ |
| Payload metadata | `results`, `image_s3_uri`, `image_description`, `img_element_list` | ≤40 KB total, ≤50 keys/vector | ✅ (tiny) |
| Top-K query | k=5 k-NN | `QueryVectors` topK ≤10,000 | ✅ |
| Vector count | COCO sample set (thousands) | ≤2B/index | ✅ |
| IaC | CfnCollection + 3 policies + custom-resource index | native `AWS::S3Vectors::VectorBucket` + `Index` | ✅ |

**Embedding model, dimension, and metadata shape are all preserved** — this is a storage-layer swap, not a data-model change. No re-embedding logic changes; vectors are byte-identical.

## 3. Behavior change we ARE making (approved): pre-filter instead of post-filter

The current read path (`generate_recommendations_fn`) runs a k-NN search for k=5 **then** applies a `post_filter` on `node` + `objective`. Because the filter runs *after* retrieval, a query can return **fewer than 5 — or zero — references** whenever the top-5 nearest images don't happen to match the requested node/objective.

S3 Vectors `QueryVectors` applies metadata filters **during** the search (pre-filter), so topK=5 returns the 5 nearest vectors *that match the filter*. This fixes the empty-references bug for free. We adopt it deliberately and note it in the PR.

## 4. What gets deleted (the simplification win)

- **The entire `create-opensearch-roles` stack** — the two AOSS assume-roles disappear. IAM collapses to `s3vectors:*` actions on the bucket/index, attached to the two Lambdas' own roles.
- **All 3 AOSS security policies** — data-access (`embed-acc-pol`), network (`embed-net-pol`), encryption (`embed-encry-pol`). S3 Vectors uses standard S3/IAM access control; Block Public Access is always on.
- **The `create_oss_embeddings_index` custom-resource Lambda + its `cr.Provider`** — replaced by the native `AWS::S3Vectors::Index` L1 resource (verified: it supports `Dimension`, `DistanceMetric=cosine`, `DataType=float32`, and `MetadataConfiguration.NonFilterableMetadataKeys`).
- **`opensearch-py` dependency** — removed from `index_data_fn`, `generate_recommendations_fn`, and the deleted custom resource.

Net: **one fewer CDK app, ~3 policies, and 1 Lambda gone**, plus a dependency dropped.

## 5. What changes (file-by-file)

### Infra
| File | Change |
|---|---|
| `create-opensearch-roles/` (whole app) | **Delete.** Remove from deploy docs / README chaining. |
| `backend-img-indexing/pace_backend/oss_indexing_db/__init__.py` | Replace `CfnCollection` + 3 policies + custom-resource index with `CfnVectorBucket` + `CfnIndex` (dimension 1024, cosine, float32, non-filterable metadata keys for the text fields). Grant `s3vectors:*` to the indexing Lambda role. Update stack outputs (bucket name + index name/ARN instead of collection endpoint/ARN). |
| `backend-img-indexing/pace_backend/oss_indexing_db/custom_resources/create_oss_embeddings_index/` | **Delete** the whole custom resource dir. |
| `backend-img-indexing/pace_backend/__init__.py` | Drop `OSSCollectionName`; add/rename params for vector bucket + index. Rewire env vars to indexer. |
| `backend-img-indexing/pace_backend/index_imgs_workflow/__init__.py` | Swap `OSS_HOST`/`OSS_EMBEDDINGS_INDEX_NAME` env for `VECTOR_BUCKET_NAME`/`VECTOR_INDEX_NAME`. |
| `backend-img-generation/pace_backend/__init__.py` | Replace the query-side AOSS params + `aoss:*` IAM with vector-bucket params + `s3vectors:GetVectors`/`QueryVectors`. Rewire `generate_recommendations_fn` env. |

### Application code
| File | Change |
|---|---|
| `.../index_imgs_workflow/index_data_fn/index.py` | Replace `opensearchpy.OpenSearch(...).index()` with boto3 `s3vectors.put_vectors()`. Vector `key` = image filename (was doc `id`); `data.float32` = embedding; `metadata` = `{node, objective, results, image_s3_uri, image_description, img_element_list}`. |
| `.../generate_recommendations_fn/index.py` | Replace `search()` k-NN + `post_filter` with `s3vectors.query_vectors(topK=5, queryVector=..., filter={node, objective}, returnMetadata=True)`. Map results (`key`/`distance`/`metadata`) to the existing `{url, metric, score, description, img_elements}` response shape. **This is where the pre-filter fix lands.** |
| 3× `requirements.txt` | Remove `opensearch-py`; ensure `boto3` recent enough for the `s3vectors` client (SDK ≥ the 2025-07-15 API; pin explicitly). |

### Data
- No live data to preserve — re-run `sample-data-generation/index_images.py` to repopulate the new index after deploy. (Bulk loader itself needs no change; it drives the same ingestion API.)

## 6. Sequence

1. **Preflight** — confirm `s3vectors` client is in the deploy env's boto3, and `AWS::S3Vectors::*` L1 resources exist in the pinned `aws-cdk-lib`. *Fallback:* if CDK lags, define the bucket/index via a thin `AwsCustomResource` on the boto3 `s3vectors` client (create/delete). us-west-2 availability confirmed.
2. **Infra** — new vector bucket + index + IAM; delete the roles stack and policies.
3. **Client code** — rewrite write + read paths; drop opensearch-py.
4. **Deploy** to us-west-2 (personal Isengard `donatoaz`), region-pinned (unset `AWS_REGION`, verify us-west-2 — per prior region-drift learning).
5. **Re-index** — run the sample bulk loader.
6. **Validate** — drive the references flow end-to-end in the UI (same Playwright harness): create campaign → references populate → matches node/objective filter (verify non-empty and correctly filtered). Screenshot as proof.
7. **Update deploy docs** — the READMEs' `--parameters` chaining changes (one fewer stack; new param names).

## 7. Effort & risk

- **~1 focused day.** Bounded blast radius: 2 Lambdas + 1 indexing stack + delete 1 stack.
- **Low risk** — storage-layer swap, no embedding/data-model change, no live data to migrate, isolated worktree/branch.
- **Main unknowns** (both cheap to resolve in preflight): CDK L1 coverage in the pinned version; exact boto3 `s3vectors` request/response field names (documented — `PutVectors`, `QueryVectors`, `GetVectors`).

## 7a. Preflight results (2026-07-26)

- **boto3 `s3vectors` client** — present in boto3 1.43.38 (all ops: `create_vector_bucket`, `create_index`, `put_vectors`, `query_vectors`, `get_vectors`, `delete_vectors`). The CDK venv ships boto3 1.28.63 (no `s3vectors`), but that only matters for the **Lambda runtime** → **pin `boto3>=1.40` (or bundle a layer)** in `index_data_fn` and `generate_recommendations_fn` requirements, since Python 3.13 Lambda's built-in boto3 may lag.
- **CDK L1 `aws_cdk.aws_s3vectors`** — **NOT** in `aws-cdk-lib==2.185.0` (predates the S3 Vectors launch). **Decision: use the generic `CfnResource` escape hatch** to emit raw `AWS::S3Vectors::VectorBucket` and `AWS::S3Vectors::Index` — CloudFormation supports these types natively, so this is fully declarative with proper create/update/delete lifecycle and **no custom-resource Lambda** (better than the fallback noted in §6). Reference `Fn::GetAtt` for the index ARN / `Ref` for wiring.
- **Immutability caveat** — every `AWS::S3Vectors::Index` property is *update-requires-Replacement*; if `IndexName` is fixed, replacement is blocked. Follow the prior S3-Vectors naming learning: don't hard-code the index name (let CFN generate it, expose via output), or hash-suffix it, so config changes can replace cleanly.

## 8. Reference facts (from AWS primary docs, 2026-07-26)

- **API version** `s3vectors-2025-07-15`. Operations: `CreateVectorBucket`, `CreateIndex`, `PutVectors` (≤500/call), `QueryVectors` (topK ≤10,000; ≤100/page), `GetVectors` (≤100), `DeleteVectors` (≤500), `ListVectors`.
- **Index (`CreateIndex` / `AWS::S3Vectors::Index`):** `DataType=float32` (only value), `Dimension` 1–4096, `DistanceMetric` `cosine|euclidean`, `MetadataConfiguration.NonFilterableMetadataKeys` (≤10). Name change/replacement rules apply (immutable index config → replacement on change).
- **Limits:** 10,000 buckets/region, 10,000 indexes/bucket, 2B vectors/index, metadata ≤40 KB & ≤50 keys/vector (filterable ≤2 KB), 1,000 Put+Delete req/s/index.
- **Metadata filtering:** all metadata filterable by default unless declared non-filterable; string/number/bool/list types.
- **CloudFormation:** `AWS::S3Vectors::VectorBucket`, `AWS::S3Vectors::Index`, `AWS::S3Vectors::VectorBucketPolicy`.
- **Integrations:** Bedrock Knowledge Bases can use an S3 Vectors index directly; snapshots can be exported to AOSS for high-QPS needs.
