import {test} from 'node:test';
import assert from 'node:assert/strict';
import {SpringWorkspace} from '../frontend/spring.js';

function fixture(){
  const auth={currentUser:{uid:'accountA',emailVerified:true,getIdToken:async()=>'test-token'}};
  const root={isConnected:true,innerHTML:'draft',setAttribute(){},querySelectorAll(){return [];},
    querySelector(){return null;},prepend(){},append(){},addEventListener(){}};
  const client=new SpringWorkspace(auth,'accountA');client.root=root;
  return {auth,root,client};
}
test('management request uses the current token and never cookies or URL credentials',async()=>{
  const old=globalThis.fetch;const f=fixture();
  try{
    globalThis.fetch=async(url,options)=>{
      assert.equal(url,'/api/spring/workspace');assert.equal(options.headers.Authorization,'Bearer test-token');
      assert.equal(options.credentials,'omit');assert.equal(options.redirect,'error');
      return {status:200,headers:{get:()=> 'text/html'},text:async()=>'<section>FICTICIO</section>'};
    };
    await f.client.load();assert.match(f.root.innerHTML,/FICTICIO/);assert.equal(f.client.busy,false);
  }finally{globalThis.fetch=old;f.client.close();}
});
test('account revocation while token is pending cannot send a request',async()=>{
  const old=globalThis.fetch;const f=fixture();let finish;let requests=0;
  f.auth.currentUser.getIdToken=()=>new Promise(resolve=>{finish=resolve;});
  try{
    globalThis.fetch=async()=>{requests++;throw Error('Must not send');};
    const request=f.client.load();f.client.close();finish('late-token');await request;
    assert.equal(requests,0);assert.equal(f.client.html,'');assert.equal(f.client.busy,false);
  }finally{globalThis.fetch=old;}
});
test('an old account response cannot replace a new account workspace',async()=>{
  const old=globalThis.fetch;const f=fixture();let finish;
  try{
    globalThis.fetch=()=>new Promise(resolve=>{finish=resolve;});
    const request=f.client.load();await new Promise(resolve=>setImmediate(resolve));
    f.client.close();f.root.innerHTML='new-account';
    finish({status:200,headers:{get:()=> 'text/html'},text:async()=>'<section>old-private-data</section>'});
    await request;assert.equal(f.root.innerHTML,'new-account');assert.equal(f.client.html,'');
  }finally{globalThis.fetch=old;}
});
test('client only forwards explicitly allowed operations',async()=>{
  const f=fixture();await assert.rejects(()=>f.client.load('admin'),/Operación inválida/);f.client.close();
});

