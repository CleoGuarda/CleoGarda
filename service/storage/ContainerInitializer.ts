import azureBlobClient from "./blob-client"

export async function setupImageContainer(): Promise<void> {
  const containerClient = azureBlobClient.getContainerClient("images")
  const createResponse = await containerClient.createIfNotExists({
    access: "blob",
  })
  if (createResponse.succeeded) {
    console.log("Image container created successfully")
  } else {
    console.log("Image container already exists")
  }
}
