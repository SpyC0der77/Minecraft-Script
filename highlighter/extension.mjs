import * as vscode from 'vscode'
import { TextDocument } from 'vscode-languageserver-textdocument'
import {
  ErrorSeverity,
  ParserContext,
  Project,
  Source,
  VanillaConfig,
} from '@spyglassmc/core'
import { getNodeJsExternals } from '@spyglassmc/core/lib/nodejs.js'
import { initialize as initializeJavaEdition } from '@spyglassmc/java-edition'

const commandLintSource = 'mcs-spyglass-command'
const validationDelayMs = 250
const supportedMinecraftVersions = [
  '1.21.2',
  '1.21.4',
  '1.21.5',
  '1.21.6',
  '1.21.7',
  '1.21.8',
  '1.21.9',
  '1.21.10',
  '1.21.11',
  '26.1',
]

let projectPromise

export function activate(context) {
  const diagnostics = vscode.languages.createDiagnosticCollection('mcs')
  const output = vscode.window.createOutputChannel('Minecraft Script')
  const timers = new Map()
  const validationTokens = new Map()
  let isUpdatingVersionFromCommand = false

  async function validate(document) {
    if (document.languageId !== 'mcs') return

    const uriKey = document.uri.toString()
    const validationToken = Symbol(uriKey)
    validationTokens.set(uriKey, validationToken)
    const isCurrentValidation = () => validationTokens.get(uriKey) === validationToken

    const commandCalls = extractCommandCalls(document.getText())
    if (commandCalls.length === 0) {
      if (isCurrentValidation()) diagnostics.set(document.uri, [])
      return
    }

    try {
      const project = await getSpyglassProject(context, output)
      if (!project.meta.hasParser('mcfunction:command')) {
        throw new Error(
          'Spyglass command parser is not available. Open View > Output > Minecraft Script for initialization logs.',
        )
      }

      const commandParser = project.meta.getParser('mcfunction:command')

      const nextDiagnostics = []

      for (const commandCall of commandCalls) {
        const errors = parseCommand(project, commandParser, commandCall.value)
        nextDiagnostics.push(
          ...errors.map((error) => toDiagnostic(document, commandCall, error)),
        )
      }

      if (isCurrentValidation()) diagnostics.set(document.uri, nextDiagnostics)
    } catch (error) {
      output.appendLine(`[Spyglass] ${error instanceof Error ? error.stack ?? error.message : String(error)}`)
      output.show(true)
      if (!isCurrentValidation()) return

      diagnostics.set(document.uri, [
        new vscode.Diagnostic(
          new vscode.Range(0, 0, 0, 1),
          'Spyglass command linting is unavailable. See the Minecraft Script output channel for details.',
          vscode.DiagnosticSeverity.Warning,
        ),
      ])
    }
  }

  function queueValidation(document) {
    if (document.languageId !== 'mcs') return

    const existingTimer = timers.get(document.uri.toString())
    if (existingTimer) clearTimeout(existingTimer)

    const timer = setTimeout(() => {
      timers.delete(document.uri.toString())
      void validate(document)
    }, validationDelayMs)

    timers.set(document.uri.toString(), timer)
  }

  async function selectMinecraftVersion() {
    const currentVersion = getMinecraftVersion()
    const selected = await vscode.window.showQuickPick(
      supportedMinecraftVersions.map((version) => ({
        label: version,
        description: version === currentVersion ? 'Current' : undefined,
      })),
      {
        matchOnDescription: true,
        placeHolder: 'Select the Minecraft version for command() linting',
        title: 'Minecraft Script Command Lint Version',
      },
    )

    if (!selected) return

    isUpdatingVersionFromCommand = true
    try {
      await vscode.workspace
        .getConfiguration('mcsHighlighter')
        .update('minecraftVersion', selected.label, getConfigurationTarget())

      await resetSpyglassProject()
      validateOpenMcsDocuments()
      void vscode.window.showInformationMessage(`Minecraft Script command linting now targets Minecraft ${selected.label}.`)
    } finally {
      isUpdatingVersionFromCommand = false
    }
  }

  function validateOpenMcsDocuments() {
    for (const document of vscode.workspace.textDocuments) queueValidation(document)
  }

  output.appendLine(
    `Minecraft Script extension activated. Command lint version: ${getMinecraftVersion()}.`,
  )

  context.subscriptions.push(
    diagnostics,
    output,
    vscode.commands.registerCommand('mcsHighlighter.showOutput', () => output.show(true)),
    vscode.commands.registerCommand('mcsHighlighter.selectMinecraftVersion', selectMinecraftVersion),
    vscode.workspace.onDidOpenTextDocument(queueValidation),
    vscode.workspace.onDidChangeTextDocument((event) => queueValidation(event.document)),
    vscode.workspace.onDidChangeConfiguration((event) => {
      if (!event.affectsConfiguration('mcsHighlighter.minecraftVersion')) return
      if (isUpdatingVersionFromCommand) return

      void resetSpyglassProject().then(validateOpenMcsDocuments)
    }),
    vscode.workspace.onDidCloseTextDocument((document) => {
      diagnostics.delete(document.uri)
      validationTokens.delete(document.uri.toString())
      const timer = timers.get(document.uri.toString())
      if (timer) clearTimeout(timer)
      timers.delete(document.uri.toString())
    }),
  )

  validateOpenMcsDocuments()
}

export async function deactivate() {
  await resetSpyglassProject()
}

async function getSpyglassProject(context, output) {
  if (!projectPromise) projectPromise = createSpyglassProject(context, output)

  const pendingProject = projectPromise
  try {
    return await pendingProject
  } catch (error) {
    if (projectPromise === pendingProject) projectPromise = undefined
    throw error
  }
}

async function resetSpyglassProject() {
  if (!projectPromise) return

  const pendingProject = projectPromise
  projectPromise = undefined
  const project = await pendingProject
  await project.close()
}

async function createSpyglassProject(context, output) {
  await vscode.workspace.fs.createDirectory(context.globalStorageUri)

  const cacheRoot = toFileRootUri(context.globalStorageUri)
  const projectRoots = getProjectRoots(context)
  const defaultConfig = {
    ...VanillaConfig,
    env: {
      ...VanillaConfig.env,
      gameVersion: getMinecraftVersion(),
    },
  }

  const project = new Project({
    cacheRoot,
    defaultConfig,
    externals: getNodeJsExternals({ cacheRoot }),
    initializers: [initializeJavaEdition],
    isDebugging: false,
    logger: createOutputLogger(output),
    projectRoots,
  })

  output.appendLine(`[Spyglass] Initializing command linter for Minecraft ${defaultConfig.env.gameVersion}...`)

  try {
    await project.init()
  } catch (error) {
    output.appendLine(
      `[Spyglass] Project initialization failed: ${error instanceof Error ? error.stack ?? error.message : String(error)}`,
    )
    output.show(true)
    throw error
  }

  if (!project.meta.hasParser('mcfunction:command')) {
    output.appendLine(
      '[Spyglass] Project initialized but mcfunction:command parser is missing. Command linting will not work.',
    )
    output.show(true)
  } else {
    output.appendLine('[Spyglass] Command linter ready.')
  }

  return project
}

function getMinecraftVersion() {
  return vscode.workspace
    .getConfiguration('mcsHighlighter')
    .get('minecraftVersion', '1.21.2')
}

function getConfigurationTarget() {
  return vscode.workspace.workspaceFolders?.length
    ? vscode.ConfigurationTarget.Workspace
    : vscode.ConfigurationTarget.Global
}

function getProjectRoots(context) {
  const workspaceRoots = vscode.workspace.workspaceFolders?.map((folder) => asRootUri(folder.uri)) ?? []
  if (workspaceRoots.length > 0) return workspaceRoots

  return [asRootUri(context.extensionUri)]
}

function asRootUri(uri) {
  const value = typeof uri === 'string' ? uri : uri.toString()
  return value.endsWith('/') ? value : `${value}/`
}

function toFileRootUri(uri) {
  if (typeof uri !== 'string' && uri.scheme !== 'file') {
    return asRootUri(vscode.Uri.file(uri.fsPath))
  }

  return asRootUri(uri)
}

function createOutputLogger(output) {
  return {
    error(data, ...args) {
      output.appendLine(formatLog('error', data, args))
    },
    info(data, ...args) {
      output.appendLine(formatLog('info', data, args))
    },
    log(data, ...args) {
      output.appendLine(formatLog('log', data, args))
    },
    warn(data, ...args) {
      output.appendLine(formatLog('warn', data, args))
    },
  }
}

function formatLog(level, data, args) {
  const values = [data, ...args].map((value) => {
    if (value instanceof Error) return value.stack ?? value.message
    if (typeof value === 'string') return value

    try {
      return JSON.stringify(value)
    } catch {
      return String(value)
    }
  })

  return `[Spyglass:${level}] ${values.join(' ')}`
}

function parseCommand(project, commandParser, command) {
  const uri = `mcs-command-lint:///${encodeURIComponent(command)}.mcfunction`
  const document = TextDocument.create(uri, 'mcfunction', 1, command)
  const context = ParserContext.create(project, { doc: document })
  const source = new Source(command)
  const node = commandParser(source, context)

  return [
    ...context.err.dump(),
    ...(Array.isArray(node?.parserErrors) ? node.parserErrors : []),
  ]
}

function toDiagnostic(document, commandCall, error) {
  const startOffset = mapCommandOffset(commandCall, error.range.start)
  const endOffset = Math.max(
    mapCommandOffset(commandCall, error.range.end),
    startOffset + 1,
  )

  const diagnostic = new vscode.Diagnostic(
    new vscode.Range(document.positionAt(startOffset), document.positionAt(endOffset)),
    error.message,
    toDiagnosticSeverity(error.severity),
  )

  diagnostic.source = commandLintSource
  return diagnostic
}

function mapCommandOffset(commandCall, offset) {
  if (offset <= 0) return commandCall.boundaries[0]
  if (offset >= commandCall.boundaries.length) {
    return commandCall.boundaries[commandCall.boundaries.length - 1]
  }

  return commandCall.boundaries[offset]
}

function toDiagnosticSeverity(severity) {
  switch (severity) {
    case ErrorSeverity.Hint:
      return vscode.DiagnosticSeverity.Hint
    case ErrorSeverity.Information:
      return vscode.DiagnosticSeverity.Information
    case ErrorSeverity.Warning:
      return vscode.DiagnosticSeverity.Warning
    case ErrorSeverity.Error:
    default:
      return vscode.DiagnosticSeverity.Error
  }
}

function extractCommandCalls(text) {
  const commands = []
  let index = 0

  while (index < text.length) {
    const char = text[index]
    const next = text[index + 1]

    if (char === '/' && next === '/') {
      index = skipLineComment(text, index + 2)
      continue
    }

    if (char === '/' && next === '*') {
      index = skipBlockComment(text, index + 2)
      continue
    }

    if (isQuote(char)) {
      index = skipString(text, index)
      continue
    }

    if (isIdentifierStart(char)) {
      const identifierStart = index
      index = readIdentifier(text, index)
      const identifier = text.slice(identifierStart, index)

      if (identifier !== 'command') continue

      const call = readCommandCall(text, index)
      if (call) {
        commands.push(call)
        index = call.end
      }

      continue
    }

    index += 1
  }

  return commands
}

function readCommandCall(text, index) {
  let cursor = skipWhitespace(text, index)
  if (text[cursor] !== '(') return undefined

  cursor = skipWhitespace(text, cursor + 1)
  if (!isQuote(text[cursor])) return undefined

  return readString(text, cursor)
}

function readString(text, quoteIndex) {
  const quote = text[quoteIndex]
  const boundaries = [quoteIndex + 1]
  let value = ''
  let cursor = quoteIndex + 1

  while (cursor < text.length) {
    const char = text[cursor]

    if (char === quote) {
      boundaries[value.length] = cursor
      return {
        boundaries,
        end: cursor + 1,
        value,
      }
    }

    if (char === '\\') {
      const escape = readEscape(text, cursor)
      value += escape.value
      boundaries[value.length] = escape.end
      cursor = escape.end
      continue
    }

    value += char
    boundaries[value.length] = cursor + 1
    cursor += 1
  }

  boundaries[value.length] = cursor
  return {
    boundaries,
    end: cursor,
    value,
  }
}

function readEscape(text, start) {
  const escaped = text[start + 1]
  if (escaped === undefined) return { end: start + 1, value: '\\' }

  if (escaped === 'u') {
    const hex = text.slice(start + 2, start + 6)
    if (/^[0-9a-fA-F]{4}$/.test(hex)) {
      return {
        end: start + 6,
        value: String.fromCharCode(Number.parseInt(hex, 16)),
      }
    }
  }

  const escapes = {
    '"': '"',
    "'": "'",
    '\\': '\\',
    b: '\b',
    f: '\f',
    n: '\n',
    r: '\r',
    t: '\t',
    v: '\v',
  }

  return {
    end: start + 2,
    value: escapes[escaped] ?? escaped,
  }
}

function skipLineComment(text, index) {
  const newline = text.indexOf('\n', index)
  return newline === -1 ? text.length : newline + 1
}

function skipBlockComment(text, index) {
  const end = text.indexOf('*/', index)
  return end === -1 ? text.length : end + 2
}

function skipString(text, quoteIndex) {
  return readString(text, quoteIndex).end
}

function skipWhitespace(text, index) {
  let cursor = index
  while (/\s/.test(text[cursor] ?? '')) cursor += 1
  return cursor
}

function readIdentifier(text, index) {
  let cursor = index + 1
  while (isIdentifierPart(text[cursor])) cursor += 1
  return cursor
}

function isQuote(char) {
  return char === '"' || char === "'" || char === '`'
}

function isIdentifierStart(char) {
  return /[A-Za-z_]/.test(char ?? '')
}

function isIdentifierPart(char) {
  return /[A-Za-z0-9_-]/.test(char ?? '')
}
