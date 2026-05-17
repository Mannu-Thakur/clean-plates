export function formDataObject(
  form: HTMLFormElement
): Record<string, string | boolean> {
  const data = new FormData(form);
  const result: Record<string, string | boolean> = {};
  for (const [key, value] of data.entries()) {
    result[key] = value instanceof File ? value.name : value.toString();
  }
  for (const element of Array.from(form.elements)) {
    if (element instanceof HTMLInputElement && element.type === 'checkbox') {
      result[element.name] = element.checked;
    }
  }
  return result;
}

export function parseJson<T>(value: string, fallback: T): T {
  try {
    return JSON.parse(value) as T;
  } catch {
    return fallback;
  }
}
