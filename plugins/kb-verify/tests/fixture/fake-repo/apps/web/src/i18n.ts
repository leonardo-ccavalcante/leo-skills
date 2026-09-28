import en from '../locales/en.json';
import es from '../locales/es.json';
import ptBR from '../locales/pt-BR.json';

const catalogs = { en, es, 'pt-BR': ptBR } as const;

export type Locale = keyof typeof catalogs;

let current: Locale = 'en';

/** Called once at boot with the workspace locale; `en` is the fallback. */
export function setLocale(locale: Locale): void {
  current = locale;
}

function lookup(catalog: unknown, key: string): string | undefined {
  let node: unknown = catalog;
  for (const part of key.split('.')) {
    if (node === null || typeof node !== 'object' || !(part in (node as object))) return undefined;
    node = (node as Record<string, unknown>)[part];
  }
  return typeof node === 'string' ? node : undefined;
}

/**
 * Resolves a dotted key such as `billing.cancel.ok` in the current locale,
 * falling back to English, then to the key itself. `{{name}}` placeholders
 * are replaced from `vars`.
 */
export function t(key: string, vars: Record<string, string | number> = {}): string {
  const raw = lookup(catalogs[current], key) ?? lookup(catalogs.en, key) ?? key;
  return raw.replace(/\{\{(\w+)\}\}/g, (_, name: string) => String(vars[name] ?? `{{${name}}}`));
}
