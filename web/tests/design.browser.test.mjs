// Real browser + local Firebase emulators only. No production accounts or mail.
import {before,after,test} from 'node:test';
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {mkdir,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {chromium,expect} from '@playwright/test';
import {initializeApp,deleteApp} from 'firebase/app';
import {getAuth,connectAuthEmulator,applyActionCode,signInWithEmailAndPassword,createUserWithEmailAndPassword,sendEmailVerification,reload} from 'firebase/auth';
import {getFirestore,connectFirestoreEmulator} from 'firebase/firestore';
import {AccountRepository} from '../frontend/repository.js';

const base='http://localhost:8002',projectId='demo-dispensalud-web';
const email=`ficticio-diseno-${crypto.randomUUID()}@example.test`,password='Emulador-diseno-2026';
const output=resolve('../previews/design-correction');
let server,browser,context,page,nodeApp,auth,repo,patient,treatment,logs='';
async function ready(){await expect(page.locator('#app')).toHaveAttribute('aria-busy','false');}
async function route(path){await page.goto(base+path);await ready();}
async function save(){await page.getByRole('button',{name:'Confirmar y guardar',exact:true}).click();await expect(page.locator('#editor')).not.toBeVisible();await ready();}
async function screenshot(name){await page.screenshot({path:resolve(output,name+'.png'),fullPage:true,animations:'disabled'});}
async function verifyEmail(email){
  const inbox=await(await fetch(`http://127.0.0.1:9098/emulator/v1/projects/${projectId}/oobCodes`)).json();
  const code=inbox.oobCodes.find(code=>code.email===email&&code.requestType==='VERIFY_EMAIL');assert(code);
  await applyActionCode(auth,code.oobCode);
}

before(async()=>{
  assert(process.env.FIRESTORE_EMULATOR_HOST,'Run with npm run test:browser (emulators only).');
  await mkdir(output,{recursive:true});await mkdir('build',{recursive:true});
  try{await fetch(base+'/salud/');throw Error('Port 8002 is already occupied; leave that service untouched.');}catch(error){if(!error.cause)throw error;}
  server=spawn(resolve('.venv/Scripts/python.exe'),['manage.py','runserver','127.0.0.1:8002','--noreload'],{cwd:process.cwd(),env:{...process.env,DJANGO_DEBUG:'1',DISPENSALUD_FIREBASE_EMULATORS:'1'},windowsHide:true});
  server.stdout.on('data',chunk=>logs+=chunk);server.stderr.on('data',chunk=>logs+=chunk);
  let started=false;
  for(let attempt=0;attempt<100;attempt++){try{const response=await fetch(base+'/salud/');if(response.ok){started=true;break;}}catch{}await new Promise(resolve=>setTimeout(resolve,100));}
  assert(started,'Temporary Django server did not start: '+logs);
  browser=await chromium.launch({headless:true,executablePath:process.env.DISPENSALUD_BROWSER??'C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe'});
  context=await browser.newContext({viewport:{width:1440,height:1000},deviceScaleFactor:1});page=await context.newPage();
  nodeApp=initializeApp({projectId,apiKey:'demo-key'},'design-browser-client');auth=getAuth(nodeApp);connectAuthEmulator(auth,'http://127.0.0.1:9098',{disableWarnings:true});
}, {timeout:30000});
after(async()=>{
  await browser?.close();await deleteApp(nodeApp).catch(()=>{});
  if(server?.pid){await new Promise(resolve=>{const kill=spawn('taskkill.exe',['/PID',String(server.pid),'/T','/F'],{windowsHide:true});kill.on('exit',resolve);});}
  await writeFile('build/design-browser-server.log',logs);
});

test('original web account composition: registration, validation, email verification and restoration', {timeout:60000},async()=>{
  await route('/cuenta/crear/');
  await page.getByLabel('Nombre completo',{exact:true}).fill('FICTICIO · Diseño web');
  await page.locator('input[name="profile"][value="Cuidador"]').check();
  await page.getByLabel('Correo electrónico',{exact:true}).fill(email);
  await page.getByLabel('Contraseña',{exact:true}).fill(password);
  await page.getByLabel('Confirmar contraseña',{exact:true}).fill('Otro-valor-ficticio');
  await page.locator('input[name="accept"]').check();
  await page.getByRole('button',{name:'Crear mi cuenta →',exact:true}).click();
  await expect(page.locator('.form-message')).toHaveText('Las contraseñas no coinciden.');
  await page.getByLabel('Confirmar contraseña',{exact:true}).fill(password);
  await page.getByRole('button',{name:'Crear mi cuenta →',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Verificar correo',exact:true})).toBeVisible();
  await expect(page.locator('.main-nav')).toBeVisible();await expect(page.locator('.integration-footer')).toBeVisible();
  await verifyEmail(email);await page.getByRole('button',{name:'Ya verifiqué mi correo',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Cuidar empieza aquí.',exact:true})).toBeVisible();await ready();
  await signInWithEmailAndPassword(auth,email,password);await auth.currentUser.getIdToken(true);
  const db=getFirestore(nodeApp);connectFirestoreEmulator(db,'127.0.0.1',8089);repo=new AccountRepository(db,auth.currentUser.uid);
  await expect.poll(async()=>(await repo.load()).preferences[0]?.body.profile).toBe('Cuidador');
  await page.reload();await expect(page.getByRole('heading',{name:'Cuidar empieza aquí.',exact:true})).toBeVisible();await ready();
  await screenshot('firebase-panel-empty-desktop');
});

test('original web cards and dialogs preserve patients, treatment planning, manual history and conflict resolution',{timeout:60000},async()=>{
  await route('/pacientes/');await page.locator('[data-action="new-patient"]').first().click();
  await page.getByLabel('Nombre completo',{exact:true}).fill('FICTICIO · Paciente diseño');await page.getByLabel('Edad',{exact:true}).fill('65');
  await page.getByLabel('Contacto de emergencia',{exact:true}).fill('Contacto ficticio');await page.locator('textarea[name="notas"]').fill('Fixture de emulador');await save();
  patient=(await repo.load()).patients[0];
  await route('/tratamientos/');await page.locator('[data-action="new-treatment"]').click();
  await page.getByLabel('Medicamento',{exact:true}).fill('FICTICIO · Tratamiento diseño');await page.getByLabel('Dosis indicada',{exact:true}).fill('Pauta ficticia de prueba');
  await page.locator('input[name="horarios"]').fill('20:00');await save();
  let data=await repo.load();treatment=data.treatments[0];assert.equal(data.doseEvents.filter(d=>!d.deleted).length,7);
  const at=Date.now()-3600000;
  await repo.save('doseEvents','manual-design-fixture',{patientId:patient.id,treatmentId:treatment.id,fechaHoraProgramada:at,fechaHoraReal:null,estado:'PENDING'});
  await route('/historial/');await page.locator('[data-action="manual"][data-id="manual-design-fixture"]').click();
  await page.locator('#editor input[type="checkbox"]').check();await save();
  data=await repo.load();assert.equal(data.doseEvents.find(d=>d.id==='manual-design-fixture').body.recordSource,'MANUAL');
  await route('/pacientes/');await page.locator('[data-action="edit-patient"]').click();await page.locator('textarea[name="notas"]').fill('Borrador ficticio conservado');
  const current=(await repo.load()).patients[0];await repo.save('patients',current.id,{...current.body,notas:'Edición ficticia de segundo cliente'},current);
  await page.getByRole('button',{name:'Confirmar y guardar',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Otro dispositivo guardó cambios',exact:true})).toBeVisible();
  await expect(page.locator('textarea[name="notas"]')).toHaveValue('Borrador ficticio conservado');await screenshot('firebase-conflict-desktop');
  await page.locator('#keep-draft').click();await save();
  assert.equal((await repo.load()).patients[0].body.notas,'Borrador ficticio conservado');
  await route('/panel/');await screenshot('firebase-panel-desktop');
  await route('/tratamientos/');await page.locator('[data-action="toggle-treatment"]').click();await save();
  data=await repo.load();assert.equal(data.treatments[0].body.activo,false);
  assert(data.doseEvents.filter(d=>d.body.origin==='GENERATED').every(d=>d.deleted));
  assert.equal(data.doseEvents.find(d=>d.id==='manual-design-fixture').deleted,false);
});

test('web responsive navigation, alerts, profile resources and history filters remain functional',{timeout:60000},async()=>{
  await repo.save('alerts','design-alert',{patientId:patient.id,tipo:'DOSIS_OMITIDA',mensaje:'FICTICIO · Alerta de prueba',fecha:Date.now(),leida:false});
  await route('/alertas/');await page.locator('[data-action="read-alert"]').click();await expect(page.getByText('Leída',{exact:true})).toBeVisible();
  assert.equal((await repo.load()).alerts[0].body.leida,true);
  await route('/panel/');
  const headingSize=()=>page.locator('.page-heading h1').evaluate(el=>parseFloat(getComputedStyle(el).fontSize));
  let normalSize;
  await expect.poll(async()=>normalSize=await headingSize()).toBeGreaterThan(0);
  await page.getByRole('button',{name:'Aumentar el tamaño del texto',exact:true}).click();
  await expect(page.locator('html')).toHaveClass(/large-type/);
  await expect.poll(headingSize,{message:'A+ must enlarge rem-based headings'}).toBeGreaterThan(normalSize);
  await page.locator('.sidebar [data-nav="patients"]').click();await ready();
  await page.locator('.sidebar [data-nav="panel"]').click();await ready();
  await expect.poll(headingSize,{message:'A+ must survive navigation'}).toBeGreaterThan(normalSize);
  await page.getByRole('button',{name:'Aumentar el tamaño del texto',exact:true}).click();
  await expect.poll(headingSize).toBe(normalSize);
  for(const [size,viewport] of Object.entries({mobile:{width:390,height:844},tablet:{width:768,height:1024}})){
    await page.setViewportSize(viewport);
    for(const path of ['/panel/','/pacientes/','/tratamientos/','/historial/','/alertas/','/equipo/','/perfil/']){
      await route(path);
      if(size==='mobile')await expect(page.locator('.workspace-menu')).toBeVisible();
      const layout=await page.evaluate(()=>({width:document.documentElement.scrollWidth,viewport:innerWidth,broken:[...document.images].filter(i=>i.complete&&!i.naturalWidth).length,fixedBottom:[...document.querySelectorAll('nav')].some(nav=>getComputedStyle(nav).position==='fixed'&&getComputedStyle(nav).bottom==='0px')}));
      assert(layout.width<=layout.viewport,path+' horizontal overflow');assert.equal(layout.broken,0);assert.equal(layout.fixedBottom,false);
      if(size==='mobile')await screenshot('firebase-'+path.split('/')[1]+'-mobile');
    }
    if(size==='mobile'){
      await page.getByRole('button',{name:'Aumentar el tamaño del texto',exact:true}).click();
      await expect(page.locator('html')).toHaveClass(/large-type/);
      for(const section of ['panel','patients','treatments','history','alerts','device','profile']){
        await page.locator('.workspace-menu summary').click();
        await page.locator(`.workspace-menu [data-nav="${section}"]`).click();await ready();
        await expect(page.locator('html')).toHaveClass(/large-type/);
        const layout=await page.evaluate(()=>({width:document.documentElement.scrollWidth,viewport:innerWidth,overflow:[...document.querySelectorAll('.web-workspace *')].filter(el=>el.getBoundingClientRect().right>innerWidth).map(el=>({tag:el.tagName,className:el.className,width:el.getBoundingClientRect().width})).slice(0,8)}));
        assert(layout.width<=layout.viewport,section+' A+ horizontal overflow: '+JSON.stringify(layout));
      }
      await page.getByRole('button',{name:'Aumentar el tamaño del texto',exact:true}).click();
      await expect(page.locator('html')).not.toHaveClass(/large-type/);
    }
  }
  await page.setViewportSize({width:1440,height:1000});await route('/historial/');
  await page.locator('select[data-filter="status"]').selectOption('LATE');await expect(page.getByText('Registro manual ·',{exact:false}).first()).toBeVisible();
  await screenshot('firebase-history-desktop');
  await route('/perfil/');await page.locator('input[name="profile"][value="Usuario"]').check();await page.getByRole('button',{name:'Guardar perfil',exact:true}).click();
  await expect(page.locator('.account-role')).toHaveText('Usuario');
  await route('/equipo/');await expect(page.getByRole('heading',{name:'Sin dispositivo vinculado',exact:true})).toBeVisible();await screenshot('firebase-device-desktop');
});

test('logout, password recovery and a second UID do not recover the previous account data',{timeout:60000},async()=>{
  await page.getByRole('button',{name:'Salir',exact:true}).click();await expect(page.locator('#auth-form')).toBeVisible();
  await page.getByRole('link',{name:'¿Olvidaste tu contraseña?',exact:true}).click();await page.getByLabel('Correo electrónico',{exact:true}).fill(email);
  await page.getByRole('button',{name:'Enviar enlace →',exact:true}).click();
  await expect(page.getByText('Si el correo corresponde a una cuenta, recibirás un enlace de recuperación.',{exact:true})).toBeVisible();
  const bEmail='ficticio-diseno-b-'+crypto.randomUUID()+'@example.test';const {user}=await createUserWithEmailAndPassword(auth,bEmail,password);await sendEmailVerification(user);await verifyEmail(bEmail);await reload(user);
  await route('/ingresar/');await page.getByLabel('Correo electrónico',{exact:true}).fill(bEmail);await page.getByLabel('Contraseña',{exact:true}).fill(password);
  await page.getByRole('button',{name:'Entrar a mi espacio →',exact:true}).click();await expect(page.getByRole('heading',{name:'Cuidar empieza aquí.',exact:true})).toBeVisible();await ready();
  await route('/pacientes/');await expect(page.getByRole('heading',{name:'Aún no hay pacientes',exact:true})).toBeVisible();
  assert.equal(await page.getByText('FICTICIO · Paciente diseño',{exact:true}).count(),0);
});
