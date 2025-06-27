import { AzureImageService } from "@/services/AzureImageService"

const imageService = new AzureImageService()

export interface StoredImage {
  url: string
  key: string
  uploadedAt: string
}

/**
 * Uploads (and overwrites) a File to Azure Blob Storage.
 * @param file File object to upload
 * @param containerName Optional container override
 * @returns metadata about the stored image
 */
export async function uploadImageFile(
  file: File,
  containerName?: string
): Promise<StoredImage> {
  const key = sanitizeFilename(file.name)
  const data = await file.arrayBuffer()
  const buffer = Buffer.from(data)

  try {
    const rawUrl = await imageService.uploadImage(key, buffer, file.type, containerName)
    const url = stripQueryParams(rawUrl)
    return {
      url,
      key,
      uploadedAt: new Date().toISOString(),
    }
  } catch (err: any) {
    console.error(`uploadImageFile failed for ${key}`, err)
    throw new Error(`Could not upload image: ${err.message || err}`)
  }
}

/**
 * Deletes an image blob if it exists.
 * @param key filename or blob key
 * @param containerName Optional container override
 */
export async function deleteImageFile(
  key: string,
  containerName?: string
): Promise<void> {
  try {
    const deleted = await imageService.deleteImage(key, containerName)
    if (!deleted) {
      console.warn(`deleteImageFile: blob did not exist (${key})`)
    }
  } catch (err: any) {
    console.error(`deleteImageFile failed for ${key}`, err)
    throw new Error(`Could not delete image: ${err.message || err}`)
  }
}

/** Remove query params (e.g., SAS tokens) from URL */
function stripQueryParams(url: string): string {
  const idx = url.indexOf("?")
  return idx === -1 ? url : url.slice(0, idx)
}

/** Simple filename sanitizer to remove dangerous chars */
function sanitizeFilename(name: string): string {
  return name.replace(/[^a-zA-Z0-9._-]/g, "_")
}
