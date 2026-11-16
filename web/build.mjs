import { build } from 'esbuild';
import {readFile} from 'node:fs/promises';
import postcss from 'postcss';
await build({entryPoints: ['frontend/main.js'], bundle: true, format: 'esm', target: ['es2020'], minify: true,
  outfile: 'portal/static/portal/firebase/app.js', legalComments: 'eof'});
// Reuse the original web panel styles without letting their global rules alter
// the original landing/header/account layout. No Android screen styles are used.
const panelSources=['portal/static/portal/vendor/bootstrap.min.css','portal/static/portal/app.css','portal/static/portal/product/panel.css'];
const root=postcss.parse((await Promise.all(panelSources.map(file=>readFile(file,'utf8')))).join('\n'));
root.walkRules(rule=>{
  let parent=rule.parent;
  while(parent){if(parent.type==='atrule' && /keyframes$/.test(parent.name))return;parent=parent.parent;}
  rule.selectors=rule.selectors.map(selector=>{
    if(/^(?:html|body|:root)(?=[\s.#:]|$)/.test(selector))return selector.replace(/^(?:html|body|:root)/,'.web-workspace');
    if(/^\.(?:care-app|signed-in)(?=[\s.#:]|$)/.test(selector))return '.web-workspace'+selector;
    return '.web-workspace '+selector;
  });
});
await build({stdin:{contents:root.toString(),loader:'css',resolveDir:process.cwd()},minify:true,write:true,outfile:'portal/static/portal/firebase/panel-web.css'});
