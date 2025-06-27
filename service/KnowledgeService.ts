import { Container, PatchOperation, PatchOperationType, SqlParameter, SqlQuerySpec } from "@azure/cosmos"
import { getKnowledgeContainer } from "../containers"
import { Knowledge, KnowledgeInput } from "../types"

/**
 * Internal helper: execute a query with parameters
 */
async function queryContainer<T>(
  container: Container,
  query: string,
  params: SqlParameter[] = []
): Promise<T[]> {
  const spec: SqlQuerySpec = { query, parameters: params }
  const iterator = container.items.query<T>(spec)
  const { resources } = await iterator.fetchAll()
  return resources
}

/**
 * Create a new knowledge document
 */
export async function createKnowledge(data: KnowledgeInput): Promise<Knowledge> {
  const container = await getKnowledgeContainer()
  const { resource } = await container.items.create<Knowledge>(data)
  return resource!
}

/**
 * Retrieve a single knowledge by id and partition (baseUrl)
 */
export async function getKnowledge(id: string, baseUrl: string): Promise<Knowledge | null> {
  const container = await getKnowledgeContainer()
  try {
    const { resource } = await container.item<Knowledge>(id, baseUrl).read()
    return resource || null
  } catch {
    return null
  }
}

/**
 * List all knowledge items under a given baseUrl
 */
export async function listKnowledgeByBaseUrl(baseUrl: string): Promise<Knowledge[]> {
  const container = await getKnowledgeContainer()
  return queryContainer<Knowledge>(
    container,
    "SELECT * FROM c WHERE c.baseUrl = @baseUrl",
    [{ name: "@baseUrl", value: baseUrl }]
  )
}

/**
 * Search top 10 relevant knowledge via vector distance on summaryEmbedding
 */
export async function searchKnowledgeByEmbedding(
  embedding: number[],
  threshold: number = 0.65,
  top: number = 10
): Promise<(Knowledge & { distance: number })[]> {
  const container = await getKnowledgeContainer()
  const query = `
    SELECT TOP @top c.*, 
      VectorDistance(c.summaryEmbedding, @emb) AS distance
    FROM c
    WHERE VectorDistance(c.summaryEmbedding, @emb) > @th
    ORDER BY distance ASC
  `
  const params: SqlParameter[] = [
    { name: "@emb", value: embedding },
    { name: "@th", value: threshold },
    { name: "@top", value: top }
  ]
  return queryContainer<Knowledge & { distance: number }>(container, query, params)
}

/**
 * List all knowledge tied to a specific URL
 */
export async function listKnowledgeByUrl(url: string): Promise<Knowledge[]> {
  const container = await getKnowledgeContainer()
  return queryContainer<Knowledge>(
    container,
    "SELECT * FROM c WHERE c.url = @url",
    [{ name: "@url", value: url }]
  )
}

/**
 * Update content or metadata of a knowledge document
 */
export async function updateKnowledge(
  id: string,
  baseUrl: string,
  patches: PatchOperation[]
): Promise<Knowledge | null> {
  const container = await getKnowledgeContainer()
  try {
    const { resource } = await container
      .item<Knowledge>(id, baseUrl)
      .patch(patches)
    return resource || null
  } catch {
    return null
  }
}

/**
 * Replace entire knowledge document
 */
export async function replaceKnowledge(
  id: string,
  baseUrl: string,
  updated: Partial<Knowledge>
): Promise<Knowledge | null> {
  const container = await getKnowledgeContainer()
  try {
    const { resource } = await container
      .item<Knowledge>(id, baseUrl)
      .replace({ ...updated, id, baseUrl })
    return resource || null
  } catch {
    return null
  }
}

/**
 * Delete a knowledge document
 */
export async function deleteKnowledge(id: string, baseUrl: string): Promise<boolean> {
  const container = await getKnowledgeContainer()
  try {
    await container.item(id, baseUrl).delete()
    return true
  } catch {
    return false
  }
}
