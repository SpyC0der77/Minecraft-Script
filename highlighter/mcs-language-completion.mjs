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
        const items = await buildImportPathCompletions(document, importMatch[2])
        return new vscode.CompletionList(items, false)
      }

      const wordRange = document.getWordRangeAtPosition(position, /[A-Za-z_][A-Za-z0-9_-]*/)
      const currentWord = wordRange ? document.getText(wordRange) : ''
      const charBefore = wordRange && wordRange.start.character > 0
        ? linePrefix[wordRange.start.character - 1]
        : ''

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

  for (const name of collectUserSymbols(document)) {
    if (seen.has(name) || (filter && !name.startsWith(filter))) continue
    const item = new vscode.CompletionItem(name, vscode.CompletionItemKind.Function)
    item.detail = 'user function'
    item.documentation = `User-defined function \`${name}\` in this file.`
    item.sortText = `2_${name}`
    items.push(item)
    seen.add(name)
  }

  return items
}

/**
 * @param {vscode.TextDocument} document
 * @param {string} partialPath
 * @returns {Promise<vscode.CompletionItem[]>}
 */
async function buildImportPathCompletions(document, partialPath) {
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

      if (normalizedPartial && !completionPath.startsWith(normalizedPartial) && !completionPath.includes(normalizedPartial)) {
        return undefined
      }

      const item = new vscode.CompletionItem(completionPath, vscode.CompletionItemKind.File)
      item.detail = 'import path'
      item.insertText = completionPath
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
 * @param {vscode.TextDocument} document
 * @returns {string[]}
 */
function collectUserSymbols(document) {
  const text = document.getText()
  const names = new Set()

  for (const match of text.matchAll(FUNCTION_PATTERN)) {
    names.add(match[1])
  }

  for (const match of text.matchAll(VARIABLE_PATTERN)) {
    names.add(match[1])
  }

  return [...names].sort()
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
