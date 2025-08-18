import { AzureImageService } from "@/services/AzureImageService"

const imageService = new AzureImageService()

export interface StoredImage {
  url: string
  key: string
  uploadedAt: string
  contentType?: string
}

/**
 * Uploads a file to Azure Blob Storage with optional container.
 */
export async function uploadImageFile(
  file: File,
  containerName?: string
): Promise<StoredImage> {
  const key = sanitizeFilename(file.name)
  const data = await file.arrayBuffer()
  const buffer = Buffer.from(data)
  const mimeType = file.type || "application/octet-stream"

  try {
    const rawUrl = await imageService.uploadImage(key, buffer, mimeType, containerName)
    const cleanUrl = stripQueryParams(rawUrl)

    return {
      url: cleanUrl,
      key,
      uploadedAt: new Date().toISOString(),
      contentType: mimeType,
    }
  } catch (err: any) {
    console.error(`[uploadImageFile] Failed to upload "${key}":`, err)
    throw new Error(`Could not upload image: ${err.message || "unknown error"}`)
  }
}

/**
 * Deletes an image blob from Azure.
 */
export async function deleteImageFile(
  key: string,
  containerName?: string
): Promise<void> {
  try {
    const wasDeleted = await imageService.deleteImage(key, containerName)
    if (!wasDeleted) {
      console.warn(`[deleteImageFile] Blob not found: "${key}"`)
    }
  } catch (err: any) {
    console.error(`[deleteImageFile] Error deleting "${key}":`, err)
    throw new Error(`Could not delete image: ${err.message || "unknown error"}`)
  }
}

/**
 * Removes query params (e.g., SAS tokens) from Azure URLs.
 */
function stripQueryParams(url: string): string {
  const idx = url.indexOf("?")
  return idx === -1 ? url : url.slice(0, idx)
}

/**
 * Sanitizes filenames to avoid path traversal or special chars.
 * Preserves alphanumerics, dashes, underscores and dots.
 */
function sanitizeFilename(name: string): string {
  const cleaned = name.replace(/[^a]()
