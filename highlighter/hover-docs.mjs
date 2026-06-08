import * as vscode from 'vscode'

/** @typedef {{ syntax: string, detail?: string, description: string }} HoverDoc */

/** @type {Record<string, HoverDoc>} */
export const KEYWORDS = {
  var: {
    syntax: 'var <name> = <value>',
    detail: 'keyword',
    description: 'Declares a mutable variable.',
  },
  const: {
    syntax: 'const <name> = <value>',
    detail: 'keyword',
    description: 'Declares a constant binding.',
  },
  set: {
    syntax: 'set <name> = <value>',
    detail: 'keyword',
    description: 'Assigns a new value to an existing variable.',
  },
  if: {
    syntax: 'if (<condition>) { ... } else { ... }',
    detail: 'keyword',
    description: 'Conditional branch.',
  },
  else: {
    syntax: 'else { ... }',
    detail: 'keyword',
    description: 'Alternative branch for an `if` statement.',
  },
  for: {
    syntax: 'for (<name> in <iterable>) { ... }',
    detail: 'keyword',
    description: 'Iterates over each item in a list or range.',
  },
  in: {
    syntax: 'for (<name> in <iterable>)',
    detail: 'keyword',
    description: 'Used with `for` to iterate over a list or `range()` result.',
  },
  while: {
    syntax: 'while (<condition>) { ... }',
    detail: 'keyword',
    description: 'Repeats a block while the condition is true.',
  },
  async: {
    syntax: 'async while (<condition>) { ... }',
    detail: 'keyword',
    description: 'Runs a while loop asynchronously across ticks.',
  },
  function: {
    syntax: 'function <name>(<params>) { ... }',
    detail: 'keyword',
    description: 'Declares a user function. Use `on` after the signature to bind an advancement event.',
  },
  on: {
    syntax: 'function <name>() on "<advancement criterion>" { ... }',
    detail: 'keyword',
    description: 'Registers the function to run when the given advancement criterion triggers.',
  },
  return: {
    syntax: 'return <value>',
    detail: 'keyword',
    description: 'Returns a value from the current function.',
  },
  import: {
    syntax: 'import "<path>" [as <alias>]',
    detail: 'keyword',
    description: 'Imports functions from another `.mcs` file.',
  },
  as: {
    syntax: 'import "<path>" as <alias>',
    detail: 'keyword',
    description: 'Gives an imported module a local alias.',
  },
  true: {
    syntax: 'true',
    detail: 'literal',
    description: 'Boolean true value.',
  },
  false: {
    syntax: 'false',
    detail: 'literal',
    description: 'Boolean false value.',
  },
  null: {
    syntax: 'null',
    detail: 'literal',
    description: 'Null value.',
  },
}

/** @type {Record<string, HoverDoc>} */
export const BUILTINS = {
  command: {
    syntax: 'function command(command: string): null',
    detail: 'builtin',
    description: 'Runs a raw Minecraft command string. The string is validated by Spyglass.',
  },
  log: {
    syntax: 'function log(...values: any[]): null',
    detail: 'builtin',
    description: 'Logs up to 5 values to chat (via tellraw) when compiled.',
  },
  tellraw: {
    syntax: 'function tellraw(target: string, message: TextComponent): null',
    detail: 'builtin',
    description: 'Sends a text component message to the given target selector.',
  },
  text: {
    syntax: 'function text(initial?: string): TextComponent',
    detail: 'builtin',
    description: 'Creates a text component. Chain methods like `.text()`, `.color()`, and `.bold()`.',
  },
  title: {
    syntax: 'function title(target: string, mode: string, message: TextComponent): null',
    detail: 'builtin',
    description: 'Shows a title, subtitle, or actionbar. `mode` is `"title"`, `"subtitle"`, or `"actionbar"`.',
  },
  title_times: {
    syntax: 'function title_times(target: string, fadeIn: number, stay: number, fadeOut: number): null',
    detail: 'builtin',
    description: 'Sets title fade-in, stay, and fade-out durations in ticks.',
  },
  give_item: {
    syntax: 'function give_item(item: string, components?: string, count?: number): null',
    detail: 'builtin',
    description: 'Gives the executing player an item. `components` is SNBT without outer braces.',
  },
  give_clickable_item: {
    syntax: 'function give_clickable_item(onClick: function, name?: string, customModelData?: string | number): null',
    detail: 'builtin',
    description: 'Gives a clickable item that runs the given function when used.',
  },
  concatenate: {
    syntax: 'function concatenate(a: string, b: string): string',
    detail: 'builtin',
    description: 'Concatenates two strings and returns the result.',
  },
  append: {
    syntax: 'function append(list: list, value: any): null',
    detail: 'builtin',
    description: 'Appends a value to the end of a list.',
  },
  range: {
    syntax: 'function range(bound: number): list',
    detail: 'builtin',
    description: 'Returns a list of numbers from `0` to `bound - 1`.',
  },
  get_block: {
    syntax: 'function get_block(x: string | number, y: string | number, z: string | number): string',
    detail: 'builtin',
    description: 'Reads the block ID at the given coordinates.',
  },
  set_block: {
    syntax: 'function set_block(block: string, x: string | number, y: string | number, z: string | number): null',
    detail: 'builtin',
    description: 'Places a block at the given coordinates.',
  },
  raycast_block: {
    syntax: 'function raycast_block(onHit: function, distance: number, onStep?: function): null',
    detail: 'builtin',
    description: 'Raycasts along the executor\'s look direction and calls `onHit` when a block is found.',
  },
  raycast_entity: {
    syntax: 'function raycast_entity(onHit: function, distance: number, onStep?: function): null',
    detail: 'builtin',
    description: 'Raycasts along the executor\'s look direction and calls `onHit` when an entity is found.',
  },
}

/** @type {Record<string, HoverDoc>} */
export const METHODS = {
  text: {
    syntax: '.text(content: string): TextComponent',
    detail: 'TextComponent method',
    description: 'Sets the text content of this component.',
  },
  color: {
    syntax: '.color(name: string): TextComponent',
    detail: 'TextComponent method',
    description: 'Sets a named color (for example `"gold"` or `"#FFAA00"`).',
  },
  font: {
    syntax: '.font(id: string): TextComponent',
    detail: 'TextComponent method',
    description: 'Sets the font resource location.',
  },
  insertion: {
    syntax: '.insertion(text: string): TextComponent',
    detail: 'TextComponent method',
    description: 'Sets text inserted into chat when the component is shift-clicked.',
  },
  bold: {
    syntax: '.bold(): TextComponent',
    detail: 'TextComponent method',
    description: 'Enables bold formatting.',
  },
  italic: {
    syntax: '.italic(): TextComponent',
    detail: 'TextComponent method',
    description: 'Enables italic formatting.',
  },
  underlined: {
    syntax: '.underlined(): TextComponent',
    detail: 'TextComponent method',
    description: 'Enables underline formatting.',
  },
  strikethrough: {
    syntax: '.strikethrough(): TextComponent',
    detail: 'TextComponent method',
    description: 'Enables strikethrough formatting.',
  },
  obfuscated: {
    syntax: '.obfuscated(): TextComponent',
    detail: 'TextComponent method',
    description: 'Enables obfuscated (random character) formatting.',
  },
  translate: {
    syntax: '.translate(key: string): TextComponent',
    detail: 'TextComponent method',
    description: 'Uses a translation key instead of literal text.',
  },
  append: {
    syntax: '.append(other: TextComponent): TextComponent',
    detail: 'TextComponent method',
    description: 'Appends another text component to this one.',
  },
  click_run: {
    syntax: '.click_run(command: string): TextComponent',
    detail: 'TextComponent method',
    description: 'Runs a command when the text is clicked.',
  },
  click_suggest: {
    syntax: '.click_suggest(command: string): TextComponent',
    detail: 'TextComponent method',
    description: 'Suggests a command in chat when the text is clicked.',
  },
  click_open_url: {
    syntax: '.click_open_url(url: string): TextComponent',
    detail: 'TextComponent method',
    description: 'Opens a URL when the text is clicked.',
  },
  click_copy: {
    syntax: '.click_copy(text: string): TextComponent',
    detail: 'TextComponent method',
    description: 'Copies text to the clipboard when clicked.',
  },
  hover_text: {
    syntax: '.hover_text(content: string | TextComponent): TextComponent',
    detail: 'TextComponent method',
    description: 'Shows hover text when the pointer is over this component.',
  },
  hover_item: {
    syntax: '.hover_item(item: string, count?: number): TextComponent',
    detail: 'TextComponent method',
    description: 'Shows an item tooltip on hover.',
  },
}

/** @type {Record<string, HoverDoc>} */
const SELECTORS = {
  '@a': {
    syntax: '@a[...]',
    detail: 'target selector',
    description: 'All players.',
  },
  '@e': {
    syntax: '@e[...]',
    detail: 'target selector',
    description: 'All entities.',
  },
  '@p': {
    syntax: '@p[...]',
    detail: 'target selector',
    description: 'Nearest player.',
  },
  '@r': {
    syntax: '@r[...]',
    detail: 'target selector',
    description: 'Random player.',
  },
  '@s': {
    syntax: '@s[...]',
    detail: 'target selector',
    description: 'The executing entity (self).',
  },
}

const SELECTOR_PATTERN = /@(?:a|e|p|r|s)(?:\[[^\]]*\])?/g
const IDENTIFIER_PATTERN = /[A-Za-z_][A-Za-z0-9_-]*/

/**
 * @param {vscode.TextDocument} document
 * @param {vscode.Position} position
 * @returns {{ range: vscode.Range, doc: HoverDoc } | undefined}
 */
function findHoverTarget(document, position) {
  const line = position.line
  const lineText = document.lineAt(line).text
  const column = position.character

  for (const match of lineText.matchAll(SELECTOR_PATTERN)) {
    const start = match.index ?? 0
    const end = start + match[0].length
    if (column < start || column >= end) continue

    const selectorKey = match[0].split('[')[0]
    const doc = SELECTORS[selectorKey]
    if (!doc) continue

    return {
      range: new vscode.Range(line, start, line, end),
      doc,
    }
  }

  const wordRange = document.getWordRangeAtPosition(position, IDENTIFIER_PATTERN)
  if (!wordRange) return undefined

  const word = document.getText(wordRange)
  const charBefore = wordRange.start.character > 0 ? lineText[wordRange.start.character - 1] : ''

  if (charBefore === '.') {
    const methodDoc = METHODS[word]
    if (methodDoc) {
      return {
        range: new vscode.Range(line, wordRange.start.character - 1, line, wordRange.end.character),
        doc: methodDoc,
      }
    }
  }

  const builtinDoc = BUILTINS[word]
  if (builtinDoc) return { range: wordRange, doc: builtinDoc }

  const keywordDoc = KEYWORDS[word]
  if (keywordDoc) return { range: wordRange, doc: keywordDoc }

  return undefined
}

/**
 * @param {HoverDoc} doc
 * @returns {vscode.MarkdownString}
 */
function formatHoverMarkdown(doc) {
  const markdown = new vscode.MarkdownString()
  markdown.appendMarkdown('```mcs\n')
  markdown.appendMarkdown(doc.syntax)
  markdown.appendMarkdown('\n```\n\n')
  if (doc.detail) markdown.appendMarkdown(`*${doc.detail}*\n\n`)
  markdown.appendMarkdown(doc.description)
  return markdown
}

/**
 * @param {vscode.TextDocument} document
 * @param {vscode.Position} position
 * @returns {vscode.Hover | undefined}
 */
export function provideMcsHover(document, position) {
  const target = findHoverTarget(document, position)
  if (!target) return undefined

  return new vscode.Hover(formatHoverMarkdown(target.doc), target.range)
}

/**
 * @returns {vscode.HoverProvider}
 */
export function createMcsHoverProvider() {
  return {
    provideHover(document, position) {
      return provideMcsHover(document, position)
    },
  }
}
