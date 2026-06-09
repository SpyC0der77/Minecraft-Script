#!/usr/bin/env node
import { mkdirSync } from 'node:fs'
import { mkdtempSync } from 'node:fs'
import { readFileSync } from 'node:fs'
import { readdirSync, statSync } from 'node:fs'
import { join, relative, resolve } from 'node:path'
import { tmpdir } from 'node:os'
import { pathToFileURL } from 'node:url'

import {
  ErrorSeverity,
  FileNode,
  Logger,
  Project,
  VanillaConfig,
} from '@spyglassmc/core'
import { getNodeJsExternals } from '@spyglassmc/core/lib/nodejs.js'
import { initialize as initializeJavaEdition } from '@spyglassmc/java-edition'
import { initialize as initializeMcdoc } from '@spyglassmc/mcdoc'

function parseArgs(argv) {
  const flags = {
    json: false,
    mcVersion: null,
  }
  const positional = []

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index]
    if (arg === '--json') {
      flags.json = true
      continue
    }
    if (arg === '--mc-version') {
      flags.mcVersion = argv[index + 1]
      index += 1
      continue
    }
    if (arg.startsWith('--mc-version=')) {
      flags.mcVersion = arg.slice('--mc-version='.length)
      continue
    }
    positional.push(arg)
  }

  if (positional.length < 1) {
    throw new Error('Usage: node mcs-spyglass-validate.mjs [--json] [--mc-version <version>] <datapack_dir>')
  }

  return { flags, datapackDir: resolve(positional[0]) }
}

function toRootUri(path) {
  const normalized = resolve(path).replace(/\\/g, '/')
  return pathToFileURL(`${normalized}/`).href
}

function severityName(severity) {
  switch (severity) {
    case ErrorSeverity.Hint:
      return 'hint'
    case ErrorSeverity.Information:
      return 'information'
    case ErrorSeverity.Warning:
      return 'warning'
    case ErrorSeverity.Error:
      return 'error'
    default:
      return 'error'
  }
}

function walkFiles(rootDir) {
  const files = []
  const stack = [rootDir]
  while (stack.length > 0) {
    const current = stack.pop()
    for (const entry of readdirSync(current)) {
      const fullPath = join(current, entry)
      const stats = statSync(fullPath)
      if (stats.isDirectory()) {
        stack.push(fullPath)
        continue
      }
      files.push(fullPath)
    }
  }
  return files
}

function languageIdFor(path) {
  if (path.endsWith('.mcfunction')) return 'mcfunction'
  if (path.endsWith('.json')) return 'json'
  if (path.endsWith('.nbt')) return 'nbt'
  return null
}

async function main() {
  const { flags, datapackDir } = parseArgs(process.argv.slice(2))
  const packMetaPath = join(datapackDir, 'pack.mcmeta')
  if (!statSync(datapackDir).isDirectory() || !statSync(packMetaPath).isFile()) {
    throw new Error(`Expected a datapack directory containing pack.mcmeta at ${datapackDir}`)
  }

  const cacheRoot = toRootUri(mkdtempSync(join(tmpdir(), 'mcs-spyglass-')))
  mkdirSync(new URL(cacheRoot), { recursive: true })
  const projectRoot = toRootUri(datapackDir)
  const gameVersion = flags.mcVersion
  const diagnostics = []

  const project = new Project({
    cacheRoot,
    defaultConfig: {
      ...VanillaConfig,
      env: {
        ...VanillaConfig.env,
        ...(gameVersion ? { gameVersion } : {}),
      },
    },
    externals: getNodeJsExternals({ cacheRoot }),
    initializers: [initializeMcdoc, initializeJavaEdition],
    isDebugging: false,
    logger: Logger.create('warn'),
    projectRoots: [projectRoot],
  })

  project.on('documentErrored', ({ uri, errors }) => {
    for (const error of errors) {
      const filePath = decodeURIComponent(new URL(uri).pathname.replace(/^\/([A-Za-z]:)/, '$1'))
      const relativePath = relative(datapackDir, filePath).replace(/\\/g, '/')
      const start = error.posRange?.start
      diagnostics.push({
        file: relativePath,
        line: (start?.line ?? 0) + 1,
        column: (start?.character ?? 0) + 1,
        message: error.message,
        severity: severityName(error.severity),
      })
    }
  })

  await project.init()
  await project.ready()

  for (const filePath of walkFiles(datapackDir)) {
    const languageId = languageIdFor(filePath)
    if (!languageId) continue
    const uri = pathToFileURL(filePath).href
    const content = readFileSync(filePath, 'utf8')
    await project.onDidOpen(uri, languageId, 1, content)
    const managed = await project.ensureClientManagedChecked(uri)
    if (!managed) continue
    for (const error of FileNode.getErrors(managed.node)) {
      diagnostics.push({
        file: relative(datapackDir, filePath).replace(/\\/g, '/'),
        line: error.range.start.line + 1,
        column: error.range.start.character + 1,
        message: error.message,
        severity: severityName(error.severity),
      })
    }
  }

  await project.close()

  const unique = new Map()
  for (const diagnostic of diagnostics) {
    const key = `${diagnostic.file}:${diagnostic.line}:${diagnostic.column}:${diagnostic.message}`
    unique.set(key, diagnostic)
  }
  const result = [...unique.values()].sort((left, right) => {
    if (left.file !== right.file) return left.file.localeCompare(right.file)
    if (left.line !== right.line) return left.line - right.line
    return left.column - right.column
  })

  if (flags.json) {
    process.stdout.write(`${JSON.stringify(result)}\n`)
  } else {
    for (const diagnostic of result) {
      process.stdout.write(
        `${diagnostic.file}:${diagnostic.line}:${diagnostic.column}: ${diagnostic.message}\n`,
      )
    }
  }

  const hasErrors = result.some((diagnostic) => diagnostic.severity === 'error')
  process.exit(hasErrors ? 1 : 0)
}

main().catch((error) => {
  const message = error instanceof Error ? error.stack ?? error.message : String(error)
  if (process.argv.includes('--json')) {
    process.stdout.write(`${JSON.stringify([{ file: '', line: 0, column: 0, message, severity: 'error' }])}\n`)
  } else {
    process.stderr.write(`${message}\n`)
  }
  process.exit(1)
})
