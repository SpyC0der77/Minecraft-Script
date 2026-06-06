import {
  AstNode,
  CompleterContext,
  Hover,
  completer,
} from '@spyglassmc/core'
import { mapCommandOffset } from './command-string.mjs'

/** @type {WeakMap<import('@spyglassmc/core').Project, Promise<import('@spyglassmc/core').Project>>} */
const readyPromises = new WeakMap()

/**
 * @param {import('@spyglassmc/core').Project} project
 * @returns {Promise<import('@spyglassmc/core').Project>}
 */
export function ensureProjectReady(project) {
  if (!readyPromises.has(project)) {
    const promise = project.ready().catch((error) => {
      readyPromises.delete(project)
      throw error
    })
    readyPromises.set(project, promise)
  }

  return readyPromises.get(project)
}

/**
 * @param {import('@spyglassmc/core').Project} project
 */
export function isProjectReady(project) {
  return project.isReady
}

/**
 * @param {string} mcsUri
 * @param {number} callStartOffset
 */
export function getVirtualCommandUri(mcsUri, callStartOffset) {
  return `${mcsUri}#command-${callStartOffset}.mcfunction`
}

/**
 * @param {import('@spyglassmc/core').Project} project
 * @param {string} mcsUri
 * @param {number} callStartOffset
 * @param {string} commandText
 * @returns {Promise<import('@spyglassmc/core').DocAndNode | undefined>}
 */
export async function getVirtualCommandDoc(project, mcsUri, callStartOffset, commandText) {
  const uri = getVirtualCommandUri(mcsUri, callStartOffset)
  let managed = project.getClientManaged(uri)

  if (managed && managed.doc.getText() !== commandText) {
    project.onDidClose(uri)
    managed = undefined
  }

  if (!managed) {
    await project.onDidOpen(uri, 'mcfunction', 1, commandText)
  }

  return project.ensureClientManagedChecked(uri)
}

/**
 * @param {import('@spyglassmc/core').Project} project
 * @param {import('@spyglassmc/core').DocAndNode} managed
 * @param {number} commandOffset
 * @param {string | undefined} triggerCharacter
 */
export function getCompletions(project, managed, commandOffset, triggerCharacter) {
  const shouldComplete = project.meta.shouldComplete(
    managed.doc.languageId,
    triggerCharacter,
  )

  if (!shouldComplete) return []

  return completer.file(
    managed.node,
    CompleterContext.create(project, {
      doc: managed.doc,
      offset: commandOffset,
      triggerCharacter,
    }),
  )
}

/**
 * @param {import('@spyglassmc/core').Project} project
 * @param {import('@spyglassmc/core').DocAndNode} managed
 * @param {number} commandOffset
 * @returns {import('@spyglassmc/core').Hover | undefined}
 */
export function getCommandHover(project, managed, commandOffset) {
  let node = AstNode.findDeepestChild({ node: managed.node, needle: commandOffset })

  while (node) {
    const symbol = project.symbols.resolveAlias(node.symbol)
    if (symbol) {
      const markdown =
        `\`\`\`typescript\n(${symbol.category}${symbol.subcategory ? `/${symbol.subcategory}` : ''}) ${symbol.identifier}\n\`\`\`` +
        (symbol.desc ? `\n******\n${symbol.desc}` : '')

      return Hover.create(node.range, markdown)
    }

    if (node.hover) {
      return Hover.create(node.range, node.hover)
    }

    node = node.parent
  }

  return undefined
}

/**
 * @param {{ boundaries: number[] }} commandCall
 * @param {{ start: number, end: number }} range
 */
export function mapCommandRangeToOffsets(commandCall, range) {
  return {
    start: mapCommandOffset(commandCall, range.start),
    end: mapCommandOffset(commandCall, range.end),
  }
}
