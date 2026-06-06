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
          items.length > 0,
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

/**
 * @param {number | undefined} kind
 */
function toVscodeCompletionKind(kind) {
  switch (kind) {
    case 2:
      return vscode.CompletionItemKind.Method
    case 3:
      return vscode.CompletionItemKind.Function
    case 4:
      return vscode.CompletionItemKind.Constructor
    case 5:
      return vscode.CompletionItemKind.Field
    case 6:
      return vscode.CompletionItemKind.Variable
    case 7:
      return vscode.CompletionItemKind.Class
    case 8:
      return vscode.CompletionItemKind.Interface
    case 9:
      return vscode.CompletionItemKind.Module
    case 10:
      return vscode.CompletionItemKind.Property
    case 11:
      return vscode.CompletionItemKind.Unit
    case 12:
      return vscode.CompletionItemKind.Value
    case 13:
      return vscode.CompletionItemKind.Enum
    case 14:
      return vscode.CompletionItemKind.Keyword
    case 15:
      return vscode.CompletionItemKind.Snippet
    case 16:
      return vscode.CompletionItemKind.Color
    case 17:
      return vscode.CompletionItemKind.File
    case 18:
      return vscode.CompletionItemKind.Reference
    case 19:
      return vscode.CompletionItemKind.Folder
    case 20:
      return vscode.CompletionItemKind.EnumMember
    case 21:
      return vscode.CompletionItemKind.Constant
    case 22:
      return vscode.CompletionItemKind.Struct
    case 23:
      return vscode.CompletionItemKind.Event
    case 24:
      return vscode.CompletionItemKind.Operator
    case 25:
      return vscode.CompletionItemKind.TypeParameter
    case 1:
    default:
      return vscode.CompletionItemKind.Text
  }
}
