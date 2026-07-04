export function navigateToChat(prompt: string) {
  if (typeof window !== "undefined") {
    const encoded = encodeURIComponent(prompt);
    window.location.href = `/?q=${encoded}`;
  }
}
