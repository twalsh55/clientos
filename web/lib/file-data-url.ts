export async function readImageFileAsDataUrl(file: File): Promise<string> {
  if (!file.type.startsWith("image/")) {
    throw new Error("Choose an image file for the business logo.");
  }
  if (file.size > 512_000) {
    throw new Error("Keep the business logo under 500 KB.");
  }

  return await new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result === "string") {
        resolve(reader.result);
        return;
      }
      reject(new Error("Unable to read the business logo."));
    };
    reader.onerror = () => {
      reject(new Error("Unable to read the business logo."));
    };
    reader.readAsDataURL(file);
  });
}
