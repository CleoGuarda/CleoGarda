import { BlobServiceClient, ContainerClient, BlobClient as AzureBlobClientSDK, BlockBlobClient } from "@azure/storage-blob"

const STORAGE_URL = process.env.NEXT_PUBLIC_STORAGE_URL
const STORAGE_SAS = process.env.NEXT_PUBLIC_STORAGE_SAS
if (!STORAGE_URL || !STORAGE_SAS) {
  throw new Error("Missing NEXT_PUBLIC_STORAGE_URL or NEXT_PUBLIC_STORAGE_SAS env variables")
}

const ENDPOINT = `${STORAGE_URL}?sv=${STORAGE_SAS}`

/**
 * High-level wrapper around Azure BlobServiceClient
 */
export class AzureBlobClient {
  private svc: BlobServiceClient

  constructor(endpoint: string = ENDPOINT) {
    this.svc = new BlobServiceClient(endpoint)
  }

  /** Get or create a container client */
  async getContainer(name: string, createIfMissing = true): Promise<ContainerClient> {
    const container = this.svc.getContainerClient(name)
    if (createIfMissing) {
      const exists = await container.exists()
      if (!exists) {
        await container.create({ access: "container" })
      }
    }
    return container
  }

  /** Upload a blob (Buffer or Blob) */
  async upload(
    containerName: string,
    blobName: string,
    data: Buffer | Blob | ArrayBuffer,
    mimeType?: string
  ): Promise<string> {
    const container = await this.getContainer(containerName)
    const blockBlob: BlockBlobClient = container.getBlockBlobClient(blobName)
    await blockBlob.uploadData(data, {
      blobHTTPHeaders: mimeType ? { blobContentType: mimeType } : undefined
    })
    // Return URL without query params
    return blockBlob.url.split("?")[0]
  }

  /** Download blob content as ArrayBuffer */
  async download(containerName: string, blobName: string): Promise<ArrayBuffer> {
    const container = await this.getContainer(containerName, false)
    const blobClient: AzureBlobClientSDK = container.getBlobClient(blobName)
    const resp = await blobClient.download()
    return await resp.arrayBuffer()
  }

  /** Delete a blob if it exists */
  async delete(containerName: string, blobName: string): Promise<boolean> {
    const container = await this.getContainer(containerName, false)
    const blockBlob = container.getBlockBlobClient(blobName)
    const result = await blockBlob.deleteIfExists()
    return result.succeeded
  }

  /** List all blob names in a container */
  async list(containerName: string): Promise<string[]> {
    const container = await this.getContainer(containerName, false)
    const names: string[] = []
    for await (const blob of container.listBlobsFlat()) {
      names.push(blob.name)
    }
    return names
  }
}

// default singleton
export const azureBlobClient = new AzureBlobClient()
