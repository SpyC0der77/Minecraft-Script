#!/usr/bin/env node
import esbuild from 'esbuild'

const isWatch = process.argv.includes('--watch')

/** @type {esbuild.BuildOptions} */
const buildOptions = {
  entryPoints: ['./extension.mjs'],
  bundle: true,
  platform: 'node',
  target: 'node18',
  format: 'cjs',
  outfile: './dist/extension.js',
  external: ['vscode'],
  sourcemap: true,
  logLevel: 'info',
}

if (isWatch) {
  const context = await esbuild.context(buildOptions)
  await context.watch()
  console.info('Watching extension sources...')
} else {
  await esbuild.build(buildOptions)
  console.info('Built extension to dist/extension.js')
}
