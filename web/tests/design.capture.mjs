import {chromium} from '@playwright/test';
import {mkdir,writeFile,readFile} from 'node:fs/promises';
import {spawnSync} from 'node:child_process';
import {resolve} from 'node:path';

export const browserPath=process.env.DISPENSALUD_BROWSER ?? 'C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe';
const output=resolve('../previews/design-correction');
await mkdir(output,{recursive:true});
const render=spawnSync(resolve('.venv/Scripts/python.exe'),['tests/render_original_panel.py'],{cwd:process.cwd(),windowsHide:true,encoding:'utf8'});
if(render.status!==0)throw Error(render.stderr);
const browser=await chromium.launch({headless:true,executablePath:browserPath});
const report=[];
try {
  for(const [size,viewport] of Object.entries({desktop:{width:1440,height:1000},mobile:{width:390,height:844}})) {
    for(const [version,port] of [['original',8001],['firebase',8000]]) {
      const context=await browser.newContext({viewport,deviceScaleFactor:1});
      const page=await context.newPage();
      const errors=[];page.on('pageerror',error=>errors.push(error.message));
      for(const [name,path] of [['home','/'],['login','/ingresar/'],['register','/cuenta/crear/']]) {
        await page.goto(`http://localhost:${port}${path}`,{waitUntil:'networkidle'});
        if(version==='firebase' && name!=='home')await page.locator('#auth-form').waitFor();
        // Walk every lower section so lazy images are loaded and inspected too.
        for(const section of await page.locator('main > section').all())await section.scrollIntoViewIfNeeded();
        await page.locator('footer').scrollIntoViewIfNeeded();
        await page.evaluate(async()=>{await document.fonts.ready;await Promise.all([...document.images].map(image=>image.decode().catch(()=>{})));window.scrollTo(0,0);});
        await page.screenshot({path:resolve(output,`${version}-${name}-${size}.png`),fullPage:true,animations:'disabled'});
        const details=await page.evaluate(()=>({
          viewport:innerWidth,width:document.documentElement.scrollWidth,
          sections:[...document.querySelectorAll('main > section[id]')].map(section=>({id:section.id,heading:section.querySelector('h1,h2')?.textContent,top:Math.round(section.getBoundingClientRect().top+scrollY),height:Math.round(section.getBoundingClientRect().height)})),
          images:[...document.images].map(image=>({src:image.getAttribute('src'),loaded:image.complete&&image.naturalWidth>0})),
          font:getComputedStyle(document.body).fontFamily,background:getComputedStyle(document.body).backgroundColor,
          headerHeight:Math.round(document.querySelector('.site-header').getBoundingClientRect().height),
          account:[...document.querySelectorAll('.account-layout,.account-intro,.account-card')].map(el=>({class:el.className,x:Math.round(el.getBoundingClientRect().x),width:Math.round(el.getBoundingClientRect().width)})),
        }));
        if(details.width>viewport.width)throw Error(`${version} ${name} ${size}: horizontal overflow`);
        if(details.images.some(image=>!image.loaded))throw Error(`${version} ${name}: broken image`);
        if(errors.length)throw Error(errors.join('; '));
        report.push({version,name,size,...details});
      }
      if(size==='mobile'){
        await page.goto(`http://localhost:${port}/ingresar/`);
        await page.getByRole('button',{name:'Abrir menú',exact:true}).click();
        if(!await page.locator('#mobile-drawer').isVisible())throw Error('Original mobile menu did not open');
      }
      await context.close();
    }
  }
  for(const size of ['desktop','mobile']){
    const original=report.find(row=>row.version==='original'&&row.name==='home'&&row.size===size);
    const current=report.find(row=>row.version==='firebase'&&row.name==='home'&&row.size===size);
    if(JSON.stringify(original.sections.map(s=>s.id))!==JSON.stringify(current.sections.map(s=>s.id)))throw Error('Landing sections removed or reordered');
    if(original.font!==current.font||original.background!==current.background||original.headerHeight!==current.headerHeight)throw Error('Original typography, background or header changed');
  }
  const reference=await readFile(resolve('build/original-panel.html'),'utf8');
  for(const [size,viewport] of Object.entries({desktop:{width:1440,height:1000},mobile:{width:390,height:844}})){
    const page=await browser.newPage({viewport,deviceScaleFactor:1});
    await page.setContent(reference,{waitUntil:'networkidle'});
    await page.screenshot({path:resolve(output,`reference-panel-template-${size}.png`),fullPage:true,animations:'disabled'});
    await page.close();
  }
  await writeFile(resolve(output,'comparison.json'),JSON.stringify(report,null,2));
  console.log(`Captured ${report.length} complete pages. Same original section order, typography, background and header; no broken images or horizontal overflow.`);
}finally{await browser.close();}
