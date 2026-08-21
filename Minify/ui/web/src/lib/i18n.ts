/**
 * Resolves raw text containing optional '&key' prefix or format placeholders.
 * @param raw - The string to resolve (e.g. "&button_patch", "Hello {0}")
 * @param args - Positional arguments for {0}, {1} replacement
 * @param dict - Current localization key-value map
 */
export function resolveText(
  raw: string | undefined | null,
  args?: (string | number)[],
  dict?: Record<string, string>
): string {
  if (!raw) return '';

  let text = raw;
  if (text.startsWith('&')) {
    const key = text.slice(1);
    if (dict && key in dict) {
      text = dict[key];
    } else {
      return '';
    }
  }

  if (args && args.length > 0) {
    args.forEach((arg, index) => {
      text = text.replace(new RegExp(`\\{${index}\\}`, 'g'), String(arg));
    });
  }

  return text;
}
