import * as vscode from 'vscode'
import { findCommandCallAtOffset } from './command-string.mjs'
import {
  ensureProjectReady,
  getCompletions,
  getVirtualCommandDoc,
  mapCommandRangeToOffsets,
} from './command-spyglass.mjs'

export const COMMAND_TRIGGER_CHARACTERS = [
  ' ',
  '[',
  '=',
  '!',
  ',',
  '{',
  ':',
  '/',
  '.',
  '"',
  "'",
]

const completionSource = 'Spyglass'

/**
 * @param {() => Promise<import('@spyglassmc/core').Project>} getSpyglassProject
 * @param {vscode.OutputChannel} output
 * @returns {vscode.CompletionItemProvider}
 */
export function createCommandCompletionProvider(getSpyglassProject, output) {
  return {
    async provideCompletionItems(document, position, _token, context) {
      if (document.languageId !== 'mcs') return undefined

      const offset = document.offsetAt(position)
      const target = findCommandCallAtOffset(document.getText(), offset)
      if (!target) return undefined

      try {
        const project = await getSpyglassProject()
        if (!project.meta.hasParser('mcfunction:command')) return []

        await ensureProjectReady(project)

        const managed = await getVirtualCommandDoc(
          project,
          document.uri.toString(),
          target.call.start,
          target.call.value,
        )

        if (!managed) return []

        const items = getCompletions(
          project,
          managed,
          target.commandOffset,
          context.triggerCharacter,
        )

        return new vscode.CompletionList(
          items.map((item) => toVscodeCompletionItem(document, target.call, item)),
          false,
        )
      } catch (error) {
        output.appendLine(
          `[Spyglass] Completion failed: ${error instanceof Error ? error.stack ?? error.message : String(error)}`,
        )
        return []
      }
    },
  }
}

/**
 * VS Code does not auto-suggest inside `string.*` scopes unless
 * `editor.quickSuggestions.strings` is enabled. Trigger suggest manually
 * when the user types a Spyglass trigger character inside command().
 *
 * @returns {vscode.Disposable}
 */
export function createCommandSuggestTrigger() {
  return vscode.workspace.onDidChangeTextDocument((event) => {
    const editor = vscode.window.activeTextEditor
    if (!editor || editor.document !== event.document || event.document.languageId !== 'mcs') {
      return
    }

    for (const change of event.contentChanges) {
      if (change.rangeLength > 0 || change.text.length !== 1) continue
      if (!COMMAND_TRIGGER_CHARACTERS.includes(change.text)) continue

      const cursorOffset = change.rangeOffset + change.text.length
      if (!findCommandCallAtOffset(event.document.getText(), cursorOffset)) continue

      queueMicrotask(() => {
        if (vscode.window.activeTextEditor?.document === event.document) {
          void vscode.commands.executeCommand('editor.action.triggerSuggest')
        }
      })
      return
    }
  })
}

/**
 * @param {vscode.TextDocument} document
 * @param {{ boundaries: number[] }} commandCall
 * @param {import('@spyglassmc/core').CompletionItem} item
 */
function toVscodeCompletionItem(document, commandCall, item) {
  const mapped = mapCommandRangeToOffsets(commandCall, item.range)
  const range = new vscode.Range(
    document.positionAt(mapped.start),
    document.positionAt(mapped.end),
  )

  const completion = new vscode.CompletionItem(
    item.labelSuffix ? `${item.label}${item.labelSuffix}` : item.label,
    toVscodeCompletionKind(item.kind),
  )

  completion.range = range
  completion.source = completionSource

  if (item.detail) completion.detail = item.detail
  if (item.documentation) completion.documentation = item.documentation
  if (item.insertText !== undefined) completion.insertText = item.insertText
  if (item.sortText) completion.sortText = item.sortText
  if (item.filterText) completion.filterText = item.filterText
  if (item.deprecated) {
    completion.tags = [vscode.CompletionItemTag.Deprecated]
  }

  return completion
}

/** LSP/Spyglass CompletionItemKind values are 1-based (Text = 1). */
const spyglassCompletionKinds = [
  vscode.CompletionItemKind.Text,
  vscode.CompletionItemKind.Method,
  vscode.CompletionItemKind.Function,
  vscode.CompletionItemKind.Constructor,
  vscode.CompletionItemKind.Field,
  vscode.CompletionItemKind.Variable,
  vscode.CompletionItemKind.Class,
  vscode.CompletionItemKind.Interface,
  vscode.CompletionItemKind.Module,
  vscode.CompletionItemKind.Property,
  vscode.CompletionItemKind.Unit,
  vscode.CompletionItemKind.Value,
  vscode.CompletionItemKind.Enum,
  vscode.CompletionItemKind.Keyword,
  vscode.CompletionItemKind.Snippet,
  vscode.CompletionItemKind.Color,
  vscode.CompletionItemKind.File,
  vscode.CompletionItemKind.Reference,
  vscode.CompletionItemKind.Folder,
  vscode.CompletionItemKind.EnumMember,
  vscode.CompletionItemKind.Constant,
  vscode.CompletionItemKind.Struct,
  vscode.CompletionItemKind.Event,
  vscode.CompletionItemKind.Operator,
  vscode.CompletionItemKind.TypeParameter,
]

/**
 * @param {number | undefined} kind
 */
function toVscodeCompletionKind(kind) {
  if (kind === undefined || kind < 1 || kind > spyglassCompletionKinds.length) {
    return vscode.CompletionItemKind.Text
  }

  return spyglassCompletionKinds[kind - 1]
}
