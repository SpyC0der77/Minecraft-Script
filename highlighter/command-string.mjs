export function extractCommandCalls(text) {
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

      if (identifier !== 'command' || !isBuiltinCommandCall(text, identifierStart)) continue

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

/**
 * @param {string} text
 * @param {number} offset
 * @returns {{ call: { boundaries: number[], end: number, start: number, value: string }, commandOffset: number } | undefined}
 */
export function findCommandCallAtOffset(text, offset) {
  for (const call of extractCommandCalls(text)) {
    const contentStart = call.boundaries[0]
    const closingQuote = call.end - 1

    if (offset < contentStart || offset > closingQuote) continue

    if (offset === closingQuote) {
      return { call, commandOffset: call.value.length }
    }

    return { call, commandOffset: mapFileOffsetToCommand(call, offset) }
  }

  return undefined
}

/**
 * @param {{ boundaries: number[], value: string }} commandCall
 * @param {number} fileOffset
 */
export function mapFileOffsetToCommand(commandCall, fileOffset) {
  const boundaries = commandCall.boundaries

  for (let index = boundaries.length - 1; index >= 0; index -= 1) {
    if (fileOffset >= boundaries[index]) {
      return Math.min(index, commandCall.value.length)
    }
  }

  return 0
}

/**
 * @param {{ boundaries: number[] }} commandCall
 * @param {number} offset
 */
export function mapCommandOffset(commandCall, offset) {
  if (offset <= 0) return commandCall.boundaries[0]
  if (offset >= commandCall.boundaries.length) {
    return commandCall.boundaries[commandCall.boundaries.length - 1]
  }

  return commandCall.boundaries[offset]
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
        start: quoteIndex,
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
    start: quoteIndex,
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

function isBuiltinCommandCall(text, identifierStart) {
  let cursor = identifierStart - 1
  while (cursor >= 0 && /\s/.test(text[cursor])) cursor -= 1

  return cursor < 0 || text[cursor] !== '.'
}
