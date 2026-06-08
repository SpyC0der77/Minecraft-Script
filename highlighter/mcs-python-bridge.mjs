import { spawn } from 'node:child_process'
import * as vscode from 'vscode'

/**
 * @typedef {{ line: number, column: number, message: string, severity?: string }} McsDiagnostic
 */

/**
 * @param {vscode.OutputChannel} output
 * @returns {Promise<McsDiagnostic[]>}
 */
export async function lintMcsDocument(document, output) {
  const sourcePath = getLintSourcePath(document)
  const pythonCommand = getPythonCommand()
  const args = ['-m', 'minecraft_script', 'lint', '--json', '--stdin']

  if (sourcePath) {
    args.push('--source', sourcePath)
  }

  try {
    const stdout = await runPythonProcess(pythonCommand, args, document.getText())
    if (!stdout.trim()) return []

    const payload = JSON.parse(stdout)
    return Array.isArray(payload) ? payload : []
  } catch (error) {
    output.appendLine(
      `[MCS] Language validation failed: ${error instanceof Error ? error.stack ?? error.message : String(error)}`,
    )
    return []
  }
}

/**
 * @returns {string | undefined}
 */
function getLintSourcePath(document) {
  if (document.uri.scheme === 'file' && document.uri.fsPath) {
    return document.uri.fsPath
  }

  const configured = vscode.workspace
    .getConfiguration('mcsHighlighter')
    .get('lintSourcePath')

  return typeof configured === 'string' && configured.trim() ? configured.trim() : undefined
}

function getPythonCommand() {
  const configured = vscode.workspace
    .getConfiguration('mcsHighlighter')
    .get('pythonPath')

  if (typeof configured === 'string' && configured.trim()) {
    return configured.trim()
  }

  return process.platform === 'win32' ? 'py' : 'python3'
}

function getPythonArgs(command) {
  if (command === 'py' && process.platform === 'win32') {
    return ['-3']
  }

  return []
}

function runPythonProcess(command, args, stdinText) {
  const pythonArgs = [...getPythonArgs(command), ...args]

  return new Promise((resolve, reject) => {
    const child = spawn(command, pythonArgs, {
      stdio: ['pipe', 'pipe', 'pipe'],
      windowsHide: true,
    })

    let stdout = ''
    let stderr = ''

    child.stdout.on('data', (chunk) => {
      stdout += chunk.toString()
    })

    child.stderr.on('data', (chunk) => {
      stderr += chunk.toString()
    })

    child.on('error', (error) => {
      reject(error)
    })

    child.on('close', (code) => {
      if (code === 0 || code === 1) {
        resolve(stdout)
        return
      }

      reject(new Error(stderr.trim() || `Python lint exited with code ${code}`))
    })

    child.stdin.write(stdinText)
    child.stdin.end()
  })
}

/**
 * @param {vscode.TextDocument} document
 * @param {McsDiagnostic} diagnostic
 * @returns {vscode.Diagnostic}
 */
export function toMcsLanguageDiagnostic(document, diagnostic) {
  const line = Math.min(Math.max(diagnostic.line - 1, 0), document.lineCount - 1)
  const column = Math.max(diagnostic.column, 0)
  const lineText = document.lineAt(line).text
  const endColumn = Math.min(column + 1, lineText.length)

  const result = new vscode.Diagnostic(
    new vscode.Range(line, column, line, endColumn),
    diagnostic.message,
    vscode.DiagnosticSeverity.Error,
  )

  result.source = 'Minecraft Script'
  return result
}
