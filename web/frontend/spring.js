// Authenticated Spring MVC fragments; all identity comes from the current Firebase SDK user.
export class SpringWorkspace {
  constructor(auth, uid) {
    this.auth=auth; this.uid=uid; this.active=true; this.busy=false; this.root=null;
    this.controller=null; this.html=''; this.loaded=0; this.generation=0;
  }
  check() {
    if(!this.active || this.auth.currentUser?.uid!==this.uid || !this.auth.currentUser?.emailVerified)
      throw Error('La sesión cambió. Vuelve a ingresar.');
  }
  cancel(){this.generation++;this.controller?.abort();this.busy=false;}
  close(){this.cancel();this.active=false;this.html='';this.root=null;}
  mount(root){
    if(!root || !this.active)return;
    this.root=root;
    root.addEventListener('submit',event=>{
      const form=event.target.closest('form[data-spring-path]');
      if(!form)return;event.preventDefault();if(this.busy)return;
      const body=new URLSearchParams(new FormData(form));
      this.load(form.dataset.springPath,{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body});
    });
    root.addEventListener('click',event=>{if(event.target.closest('[data-spring-refresh]')&&!this.busy)this.load();});
    if(this.html && Date.now()-this.loaded<15000)root.innerHTML=this.html;
    else this.load();
  }
  async load(path='workspace', options={}){
    if(this.busy)return;
    const allowed={workspace:'GET',patients:'POST','patients/delete':'POST',supervision:'POST'};
    if(allowed[path] !== (options.method??'GET'))throw Error('Operación inválida.');
    const root=this.root, ticket=++this.generation;
    this.busy=true;
    root.setAttribute('aria-busy','true');
    root.querySelectorAll('button,input,select,textarea').forEach(node=>{node.dataset.springDisabled=String(node.disabled);node.disabled=true;});
    const controller=new AbortController();this.controller=controller;
    const timeout=setTimeout(()=>controller.abort(),15000);
    try{
      this.check();const token=await this.auth.currentUser.getIdToken();this.check();
      const response=await fetch('/api/spring/'+path,{...options,headers:{...options.headers,Authorization:'Bearer '+token},
        credentials:'omit',cache:'no-store',redirect:'error',signal:controller.signal});
      this.check();if(ticket!==this.generation || !root.isConnected)return;
      const type=response.headers.get('content-type')??'';
      if(type.startsWith('text/html') && [200,409,422,503].includes(response.status)){
        const html=await response.text();this.check();
        if(ticket!==this.generation || !root.isConnected)return;
        this.html=html;this.loaded=Date.now();root.innerHTML=html;
      }else{
        const result=await response.json().catch(()=>({}));
        throw Error(result.error??(response.status===401?'La sesión venció o no está verificada. Actualiza tu acceso.':'No se pudo completar la operación.'));
      }
    }catch(error){
      if(!this.active || ticket!==this.generation)return;
      let message=root.querySelector('[data-spring-error]');
      if(!message){message=document.createElement('p');message.dataset.springError='';message.className='message error';message.setAttribute('role','alert');root.prepend(message);}
      message.textContent=error.name==='AbortError'?'La conexión tardó demasiado. Actualiza para comprobar si el cambio se guardó.':error.message;
      if(!root.querySelector('[data-spring-refresh]')){
        const retry=document.createElement('button');retry.type='button';retry.dataset.springRefresh='';retry.textContent='Reintentar';root.append(retry);
      }
    }finally{
      clearTimeout(timeout);if(ticket===this.generation){this.busy=false;root.setAttribute('aria-busy','false');
        root.querySelectorAll('[data-spring-disabled]').forEach(node=>{node.disabled=node.dataset.springDisabled==='true';delete node.dataset.springDisabled;});
      }
    }
  }
}
