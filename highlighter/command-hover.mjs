import * as vscode from 'vscode'
import { findCommandCallAtOffset } from './command-string.mjs'
import {
  ensureProjectReady,
  getCommandHover,
  getVirtualCommandDoc,
  mapCommandRangeToOffsets,
} from './command-spyglass.mjs'

/**
 * @param {() => Promise<import('@spyglassmc/core').Project>} getSpyglassProject
 * @param {vscode.OutputChannel} output
 * @returns {(document: vscode.TextDocument, position: vscode.Position) => Promise<vscode.Hover | undefined>}
 */
export function provideCommandHover(getSpyglassProject, output) {
  return async function commandHover(document, position) {
    if (document.languageId !== 'mcs') return undefined

    const offset = document.offsetAt(position)
    const target = findCommandCallAtOffset(document.getText(), offset)
    if (!target) return undefined

    try {
      const project = await getSpyglassProject()
      if (!project.meta.hasParser('mcfunction:command')) return undefined

      await ensureProjectReady(project)

      const managed = await getVirtualCommandDoc(
        project,
        document.uri.toString(),
        target.call.start,
        target.call.value,
      )

      if (!managed) return undefined

      const hover = getCommandHover(project, managed, target.commandOffset)
      if (!hover) return undefined

      const markdown = new vscode.MarkdownString(hover.markdown)
      markdown.isTrusted = true

      const mapped = mapCommandRangeToOffsets(target.call, hover.range)

      return new vscode.Hover(
        markdown,
        new vscode.Range(
          document.positionAt(mapped.start),
          document.positionAt(mapped.end),
        ),
      )
    } catch (error) {
      output.appendLine(
        `[Spyglass] Hover failed: ${error instanceof Error ? error.stack ?? error.message : String(error)}`,
      )
      return undefined
    }
  }
}

/**
 * @param {() => Promise<import('@spyglassmc/core').Project>} getSpyglassProject
 * @param {vscode.OutputChannel} output
 * @param {(document: vscode.TextDocument, position: vscode.Position) => vscode.Hover | undefined} provideMcsHover
 * @returns {vscode.HoverProvider}
 */
export function createChainedHoverProvider(getSpyglassProject, output, provideMcsHover) {
  const commandHover = provideCommandHover(getSpyglassProject, output)

  return {
    async provideHover(document, position) {
      const commandResult = await commandHover(document, position)
      if (commandResult) return commandResult

      return provideMcsHover(document, position)
    },
  }
}
