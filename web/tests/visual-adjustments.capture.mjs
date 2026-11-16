// Public pages only: real browser captures; no accounts or production writes.
import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {chromium,expect} from '@playwright/test';

const base=process.env.DISPENSALUD_PREVIEW_URL??'http://localhost:8000';
const output=resolve('../previews/visual-final');
const browser=await chromium.launch({headless:true,executablePath:process.env.DISPENSALUD_BROWSER??'C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe'});
const report=[];
await mkdir(output,{recursive:true});
try{
  for(const [size,viewport] of Object.entries({desktop:{width:1440,height:1000},mobile:{width:390,height:844},small:{width:320,height:740},tablet:{width:768,height:1024}})){
    const context=await browser.newContext({viewport,deviceScaleFactor:1});
    const page=await context.newPage(),errors=[];
    page.on('pageerror',error=>errors.push(error.message));
    page.on('response',response=>{if(response.url().startsWith(base)&&response.status()>=400)errors.push(`${response.status()} ${response.url()}`);});
    const layout=()=>page.evaluate(()=>({width:document.documentElement.scrollWidth,viewport:innerWidth,broken:[...document.images].filter(image=>!image.complete||!image.naturalWidth).map(image=>image.src)}));
    const loaded=()=>page.evaluate(async()=>{await document.fonts.ready;await Promise.all([...document.images].map(image=>image.decode().catch(()=>{})));});
    const capture=async name=>{if(['desktop','mobile'].includes(size))await page.screenshot({path:resolve(output,`${name}-${size}.png`),fullPage:true,animations:'disabled'});};
    await page.goto(base+'/',{waitUntil:'networkidle'});
    for(const section of await page.locator('main > section').all())await section.scrollIntoViewIfNeeded();
    await loaded();
    assert.deepEqual(await page.locator('main > section[id]').evaluateAll(sections=>sections.map(section=>section.id)),['inicio','producto','beneficios','funcionamiento','especificaciones','galeria','faq','contacto']);
    await expect(page.locator('#beneficios .benefit-grid article')).toHaveCount(2);
    assert.deepEqual(await page.locator('#beneficios h3').allTextContents(),['Para la persona usuaria','Para el cuidador']);
    const cards=await page.locator('#beneficios article').evaluateAll(cards=>cards.map(card=>{const rect=card.getBoundingClientRect(),icon=card.querySelector('img');return {x:rect.x,y:rect.y,width:rect.width,iconWidth:icon.getBoundingClientRect().width,src:icon.getAttribute('src')};}));
    assert(cards.every(card=>card.iconWidth>=64));
    if(viewport.width>760){assert.equal(cards[0].y,cards[1].y);assert(Math.abs(cards[0].width-cards[1].width)<1);}
    else{assert.equal(cards[0].x,cards[1].x);assert(cards[1].y>cards[0].y);}
    const home=await layout();assert(home.width<=home.viewport);assert.deepEqual(home.broken,[]);
    await page.evaluate(()=>scrollTo({top:0,behavior:'instant'}));
    if(['desktop','mobile'].includes(size)){
      const clip=await page.locator('#beneficios').evaluate(section=>{const box=section.getBoundingClientRect();return {x:box.x,y:box.y+scrollY,width:box.width,height:box.height};});
      await page.screenshot({path:resolve(output,`beneficios-${size}.png`),fullPage:true,clip,animations:'disabled'});
    }
    await capture('portada-completa');
    if(viewport.width<=1100){
      await page.getByRole('button',{name:'Abrir menú',exact:true}).click();
      await expect(page.locator('#mobile-drawer')).toBeVisible();
      await page.locator('#mobile-drawer a[href="/#galeria"]').click();
      await expect(page.locator('#mobile-drawer')).not.toBeVisible();
    }
    await page.goto(base+'/ingresar/',{waitUntil:'networkidle'});
    await expect(page.locator('#auth-form')).toBeVisible();await loaded();
    await expect(page.locator('.account-product figcaption')).toHaveCount(0);
    assert(!await page.locator('body').textContent().then(text=>text.includes('Diseño del producto · La imagen no indica una conexión física.')));
    await expect(page.locator('.account-intro .role-card')).toHaveCount(2);
    await page.locator('[data-profile="Cuidador"]').click();
    await expect(page.locator('[data-profile="Cuidador"]')).toHaveAttribute('aria-current','true');
    await expect(page.getByRole('heading',{name:'Acceso del cuidador',exact:true})).toBeVisible();
    await page.locator('[data-profile="Usuario"]').click();
    await expect(page.locator('[data-profile="Usuario"]')).toHaveAttribute('aria-current','true');
    assert.equal(await page.locator('#auth-form').evaluate(form=>form.checkValidity()),false);
    const product=await page.locator('.account-product').evaluate(el=>{const box=el.getBoundingClientRect(),intro=el.closest('.account-intro').getBoundingClientRect(),card=document.querySelector('.account-card').getBoundingClientRect();return {width:box.width,height:box.height,center:box.x+box.width/2,columnCenter:intro.x+intro.width/2,gapToForm:card.y-box.bottom,viewBox:el.querySelector('svg').getAttribute('viewBox')};});
    assert(Math.abs(product.center-product.columnCenter)<1);
    const [frameX,frameY,frameWidth,frameHeight]=product.viewBox.split(' ').map(Number);
    assert(frameX<=176&&frameY<=47&&frameX+frameWidth>=508&&frameY+frameHeight>=370,'The image viewport must contain the complete visible device');
    if(size==='desktop')assert(product.width*332/frameWidth>=300,'The visible device must be large, not just its transparent canvas');
    if(size==='desktop')assert(product.width>=300&&product.width<=380);
    if(viewport.width<=760)assert(product.width<=260&&product.gapToForm<=40);
    const iconWidths=await page.locator('.profile-illustration').evaluateAll(icons=>icons.map(icon=>icon.getBoundingClientRect().width));
    assert(iconWidths.every(width=>width>=64));
    const login=await layout();assert(login.width<=login.viewport);assert.deepEqual(login.broken,[]);
    await page.evaluate(()=>scrollTo({top:0,behavior:'instant'}));await capture('acceso');
    await page.goto(base+'/cuenta/crear/',{waitUntil:'networkidle'});
    await expect(page.locator('#auth-form')).toBeVisible();await loaded();
    assert.deepEqual(await page.locator('input[name="profile"]').evaluateAll(inputs=>inputs.map(input=>input.value)),['Usuario','Cuidador']);
    await page.locator('input[name="profile"][value="Cuidador"]').check();
    await expect(page.locator('input[name="profile"][value="Cuidador"]')).toBeChecked();
    assert((await page.locator('.role-choices .profile-illustration').evaluateAll(icons=>icons.map(icon=>icon.getBoundingClientRect().width))).every(width=>width>=64));
    const registration=await layout();assert(registration.width<=registration.viewport);assert.deepEqual(registration.broken,[]);
    assert.deepEqual(errors,[]);
    report.push({size,viewport,home,cards,login,product,iconWidths,registration});
    await context.close();
  }
  await writeFile(resolve(output,'validation.json'),JSON.stringify(report,null,2));
  console.log('Public visual checks passed at 1440, 390, 320 and 768 px; real login, benefits and full-page captures saved to '+output);
}finally{await browser.close();}
