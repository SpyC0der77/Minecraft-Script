import * as path from 'node:path'
import * as vscode from 'vscode'
import { BUILTINS, KEYWORDS, METHODS } from './hover-docs.mjs'

const languageSource = 'Minecraft Script'
const FUNCTION_PATTERN = /\bfunction\s+([A-Za-z_][A-Za-z0-9_-]*)\s*\(/g
const VARIABLE_PATTERN = /\b(?:var|const)\s+([A-Za-z_][A-Za-z0-9_-]*)\b/g
const IMPORT_PATTERN = /\bimport\s+(["'])([^"']*)$/

/**
 * @returns {vscode.CompletionItemProvider}
 */
export function createMcsLanguageCompletionProvider() {
  return {
    async provideCompletionItems(document, position) {
      if (document.languageId !== 'mcs') return undefined

      const linePrefix = document.lineAt(position.line).text.slice(0, position.character)
      const importMatch = linePrefix.match(IMPORT_PATTERN)
      if (importMatch) {
        const partialStart = linePrefix.length - importMatch[2].length
        const replaceRange = new vscode.Range(
          position.line,
          partialStart,
          position.line,
          position.character,
        )
        const items = await buildImportPathCompletions(document, importMatch[2], replaceRange)
        return new vscode.CompletionList(items, false)
      }

      const wordRange = document.getWordRangeAtPosition(position, /[A-Za-z_][A-Za-z0-9_-]*/)
      const currentWord = wordRange ? document.getText(wordRange) : ''
      const charBefore = position.character > 0 ? linePrefix[position.character - 1] : ''

      const items = charBefore === '.'
        ? buildMethodCompletions(currentWord)
        : buildGeneralCompletions(document, currentWord)

      return new vscode.CompletionList(items, false)
    },
  }
}

/**
 * @param {string} filter
 * @returns {vscode.CompletionItem[]}
 */
function buildMethodCompletions(filter) {
  return Object.entries(METHODS)
    .filter(([name]) => !filter || name.startsWith(filter))
    .map(([name, doc]) => toCompletionItem(name, doc, vscode.CompletionItemKind.Method))
}

/**
 * @param {vscode.TextDocument} document
 * @param {string} filter
 * @returns {vscode.CompletionItem[]}
 */
function buildGeneralCompletions(document, filter) {
  const items = []
  const seen = new Set()

  for (const [name, doc] of Object.entries(KEYWORDS)) {
    if (filter && !name.startsWith(filter)) continue
    items.push(toCompletionItem(name, doc, vscode.CompletionItemKind.Keyword))
    seen.add(name)
  }

  for (const [name, doc] of Object.entries(BUILTINS)) {
    if (filter && !name.startsWith(filter)) continue
    items.push(toCompletionItem(name, doc, vscode.CompletionItemKind.Function))
    seen.add(name)
  }

  for (const symbol of collectUserSymbols(document)) {
    if (seen.has(symbol.name) || (filter && !symbol.name.startsWith(filter))) continue
    const isFunction = symbol.kind === 'function'
    const item = new vscode.CompletionItem(
      symbol.name,
      isFunction ? vscode.CompletionItemKind.Function : vscode.CompletionItemKind.Variable,
    )
    item.detail = isFunction ? 'user function' : 'user variable'
    item.documentation = isFunction
      ? `User-defined function \`${symbol.name}\` in this file.`
      : `User-defined variable \`${symbol.name}\` in this file.`
    item.sortText = `2_${symbol.name}`
    items.push(item)
    seen.add(symbol.name)
  }

  return items
}

/**
 * @param {vscode.TextDocument} document
 * @param {string} partialPath
 * @param {vscode.Range} replaceRange
 * @returns {Promise<vscode.CompletionItem[]>}
 */
async function buildImportPathCompletions(document, partialPath, replaceRange) {
  const files = await vscode.workspace.findFiles('**/*.mcs', '**/node_modules/**', 100)
  const sourceDir = document.uri.scheme === 'file'
    ? path.dirname(document.uri.fsPath)
    : undefined
  const normalizedPartial = partialPath.replace(/\\/g, '/')

  return files
    .map((file) => {
      const completionPath = sourceDir
        ? toImportPath(sourceDir, file.fsPath)
        : `./${vscode.workspace.asRelativePath(file).replace(/\\/g, '/')}`

      if (normalizedPartial && !matchesImportPartial(completionPath, normalizedPartial)) {
        return undefined
      }

      const item = new vscode.CompletionItem(completionPath, vscode.CompletionItemKind.File)
      item.detail = 'import path'
      item.insertText = completionPath
      item.range = replaceRange
      item.sortText = `0_${completionPath}`
      return item
    })
    .filter(Boolean)
}

function toImportPath(sourceDir, targetPath) {
  const relative = path.relative(sourceDir, targetPath).replace(/\\/g, '/')
  return relative.startsWith('.') ? relative : `./${relative}`
}

/**
 * @param {string} completionPath
 * @param {string} normalizedPartial
 * @returns {boolean}
 */
function matchesImportPartial(completionPath, normalizedPartial) {
  return completionPath === normalizedPartial
    || completionPath.startsWith(normalizedPartial)
    || completionPath.startsWith(`${normalizedPartial}/`)
    || completionPath.includes(`/${normalizedPartial}/`)
    || completionPath.endsWith(`/${normalizedPartial}`)
}

/**
 * @param {vscode.TextDocument} document
 * @returns {Array<{ name: string, kind: 'function' | 'variable' }>}
 */
function collectUserSymbols(document) {
  const text = document.getText()
  const symbols = new Map()

  for (const match of text.matchAll(FUNCTION_PATTERN)) {
    symbols.set(match[1], { name: match[1], kind: 'function' })
  }

  for (const match of text.matchAll(VARIABLE_PATTERN)) {
    if (!symbols.has(match[1])) {
      symbols.set(match[1], { name: match[1], kind: 'variable' })
    }
  }

  return [...symbols.values()].sort((left, right) => left.name.localeCompare(right.name))
}

/**
 * @param {string} label
 * @param {{ syntax: string, detail?: string, description: string }} doc
 * @param {vscode.CompletionItemKind} kind
 * @returns {vscode.CompletionItem}
 */
function toCompletionItem(label, doc, kind) {
  const item = new vscode.CompletionItem(label, kind)
  item.detail = doc.detail ?? languageSource
  item.documentation = new vscode.MarkdownString(`\`${doc.syntax}\`\n\n${doc.description}`)
  item.sortText = `1_${label}`
  return item
}
