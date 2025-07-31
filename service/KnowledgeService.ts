import {
  Container,
  PatchOperation,
  SqlParameter,
  SqlQuerySpec,
} from "@azure/cosmos"
import { getKnowledgeContainer } from "../containers"
import { Knowledge, KnowledgeInput } from "../types"

/** Execute a parameterized SQL query and return typed resources */
async function queryContainer<T>(
  query: string,
  params: SqlParameter[] = []
): Promise<T[]> {
  const container: Container = await getKnowledgeContainer()
  const spec: SqlQuerySpec = { query, parameters: params }
  try {
    const iterator = container.items.query<T>(spec)
    const { resources } = await iterator.fetchAll()
    return resources
  } catch (err) {
    console.error("Cosmos query failed:", spec, err)
    return []
  }
}

/** Create or replace a knowledge document (upsert) */
export async function upsertKnowledge(
  data: KnowledgeInput & { id: string; baseUrl: string }
): Promise<Knowledge | null> {
  const container = await getKnowledgeContainer()
  try {
    const { resource } = await container.items.upsert<Knowledge>(data)
    return resource || null
  } catch (err) {
    console.error("Upsert failed for", data.id, err)
    return null
  }
}

/** Retrieve a knowledge document by id and partition key */
export async function getKnowledge(
  id: string,
  baseUrl: string
): Promise<Knowledge | null> {
  const container = await getKnowledgeContainer()
  try {
    const { resource } = await container.item<Knowledge>(id, baseUrl).read()
    return resource || null
  } catch {
    return null
  }
}

/** List all knowledge under a baseUrl */
export async function listKnowledgeByBaseUrl(
  baseUrl: string
): Promise<Knowledge[]> {
  const query = `SELECT * FROM c WHERE c.baseUrl = @baseUrl`
  return queryContainer<Knowledge>(query, [
    { name: "@baseUrl", value: baseUrl },
  ])
}

/** List all knowledge tied to a specific URL */
export async function listKnowledgeByUrl(url: string): Promise<Knowledge[]> {
  const query = `SELECT * FROM c WHERE c.url = @url`
  return queryContainer<Knowledge>(query, [{ name: "@url", value: url }])
}

/** Search top-N knowledge by vector similarity */
export async function searchKnowledgeByEmbedding(
  embedding: number[],
  threshold = 0.65,
  top = 10
): Promise<(Knowledge & { distance: number })[]> {
  const query = `
    SELECT TOP @top c.*, 
      VectorDistance(c.summaryEmbedding, @emb) AS distance
    FROM c
    WHERE VectorDistance(c.summaryEmbedding, @emb) > @th
    ORDER BY distance ASC
  `
  return queryContainer<Knowledge & { distance: number }>(query, [
    { name: "@emb", value: embedding },
    { name: "@th", value: threshold },
    { name: "@top", value: top },
  ])
}

/** Partially update a knowledge document via PATCH */
export async function updateKnowledge(
  id: string,
  baseUrl: string,
  patches: PatchOperation[]
): Promise<Knowledge | null> {
  const container = await getKnowledgeContainer()
  try {
    const { resource } = await container.item<Knowledge>(id, baseUrl).patch(patches)
    return resource || null
  } catch (err) {
    console.error(`Patch failed for ${id}`, err)
    return null
  }
}

/** Replace an entire knowledge document */
export async function replaceKnowledge(
  id: string,
  baseUrl: string,
  updated: Partial<Knowledge>
): Promise<Knowledge | null> {
  const container = await getKnowledgeContainer()
  try {
    const doc = { ...updated, id, baseUrl }
    const { resource } = await container.item<Knowledge>(id, baseUrl).replace(doc)
    return resource || null
  } catch (err) {
    console.error(`Replace failed for ${id}`, err)
    return null
  }
}

/** Delete a knowledge document */
export async function deleteKnowledge(
  id: string,
  baseUrl: string
): Promise<boolean> {
  const container = await getKnowledgeContainer()
  try {
    await container.item(id, baseUrl).delete()
    return true
  } catch (err) {
    console.error(`Delete failed for ${id}`, err)
    return false
  }
}
