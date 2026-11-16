import { build } from 'esbuild';
await build({entryPoints: ['frontend/main.js'], bundle: true, format: 'esm', target: ['es2020'], minify: true,
  outfile: 'portal/static/portal/firebase/app.js', legalComments: 'eof'});
