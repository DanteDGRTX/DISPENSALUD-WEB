// Private photo references live in Django; neither Firestore nor URLs carry bytes/tokens.
const base='/api/photos/v1/',idPattern=/^[a-f0-9]{32}$/;
const initial=name=>String(name||'?').trim().split(/\s+/).slice(0,2).map(word=>word[0]||'').join('').toUpperCase();
export const photoInitials=initial;
const empty=subject=>({subject,state:'empty',photoId:null,reference:null,etag:'none'});
function route(subject){if(subject==='profile')return 'profile/';const id=subject.slice(8);if(!subject.startsWith('patient:')||!/^[-_A-Za-z0-9]{1,128}$/.test(id))throw Error('Paciente inválido.');return 'patients/'+encodeURIComponent(id)+'/';}
export class PhotoClient{
  constructor(auth,uid){this.auth=auth;this.uid=uid;this.active=true;this.controllers=new Set();this.urls=new Map();this.metadata=new Map();this.loaded=0;this.pending=null;this.cleanups=new Set();}
  check(){if(!this.active||this.auth.currentUser?.uid!==this.uid||!this.auth.currentUser.emailVerified)throw Error('La cuenta cambió. Vuelve a iniciar sesión.');}
  close(){this.active=false;this.controllers.forEach(controller=>controller.abort());this.urls.forEach(url=>{if(typeof url==='string')URL.revokeObjectURL(url);});this.cleanups.forEach(clean=>clean());this.metadata.clear();this.urls.clear();}
  clearEditors(){this.cleanups.forEach(clean=>clean());this.cleanups.clear();}
  async request(path,options={}){
    this.check();const user=this.auth.currentUser,token=await user.getIdToken();this.check();
    const controller=new AbortController();this.controllers.add(controller);
    const timeout=setTimeout(()=>controller.abort(),15000);
    try{
      const response=await fetch(base+path,{...options,headers:{...options.headers,Authorization:'Bearer '+token},cache:'no-store',credentials:'omit',redirect:'error',signal:controller.signal});this.check();
      if(!response.ok){const body=await response.json().catch(()=>({}));const error=Error(body.error?.message||'No se pudo completar la operación. Reintenta.');error.status=response.status;throw error;}
      if(path.startsWith('files/'))return response.blob();
      return response.json();
    }catch(error){if(error.name==='AbortError'||error instanceof TypeError)throw Error('No se pudo conectar. La selección se conserva para reintentar.');throw error;}
    finally{clearTimeout(timeout);this.controllers.delete(controller);}
  }
  async index(force=false){
    if(!force&&Date.now()-this.loaded<15000)return;
    if(this.pending)return this.pending;
    this.pending=this.request('').then(result=>{this.check();this.metadata=new Map(result.photos.map(photo=>[photo.subject,photo]));const live=new Set(result.photos.map(photo=>photo.photoId));for(const [id,url] of this.urls)if(!live.has(id)){if(typeof url==='string')URL.revokeObjectURL(url);this.urls.delete(id);}this.loaded=Date.now();}).finally(()=>this.pending=null);
    return this.pending;
  }
  async url(photo){
    if(!idPattern.test(photo.photoId)||photo.reference!=='private-photo:v1:'+photo.photoId)throw Error('Referencia de foto inválida.');
    if(!this.urls.has(photo.photoId)){
      const pending=this.request('files/'+photo.photoId+'/').then(blob=>{this.check();if(blob.type!=='image/jpeg'||blob.size>131072||![...this.metadata.values()].some(current=>current.photoId===photo.photoId))throw Error('Imagen remota inválida o sustituida.');const url=URL.createObjectURL(blob);this.urls.set(photo.photoId,url);return url;}).catch(error=>{this.urls.delete(photo.photoId);throw error;});this.urls.set(photo.photoId,pending);
    }
    return this.urls.get(photo.photoId);
  }
  async hydrate(root,force=false){
    try{
      await this.index(force);this.check();
      await Promise.all([...root.querySelectorAll('[data-photo-subject]')].map(async node=>{
        const photo=this.metadata.get(node.dataset.photoSubject);if(!photo?.photoId)return;
        try{const url=await this.url(photo);this.check();if(node.isConnected){const image=document.createElement('img');image.src=url;image.alt='';node.replaceChildren(image);}}catch{/* Initials remain; retry on refresh, never use arbitrary remote URLs. */}
      }));
    }catch{/* A photo service outage never hides the existing care workspace. */}
  }
  mountEditor(root,subject,name){
    let selected=null,preview=null,current=empty(subject),mutation=null,blocked=false,busy=false;
    root.innerHTML='<div class="photo-preview" aria-label="Vista previa de la foto"></div><label>Seleccionar imagen<input type="file" accept="image/jpeg,image/png,image/webp"></label><p class="fine">JPEG, PNG o WebP · Hasta 2 MiB. La foto se comparte solo al pulsar Subir.</p><div class="photo-actions"><button type="button" data-upload>Subir foto</button><button type="button" class="secondary" data-delete>Eliminar foto compartida</button><button type="button" class="text-button" data-refresh>Actualizar referencia</button></div><p role="status" class="photo-status">Cargando referencia…</p>';
    const input=root.querySelector('input'),display=root.querySelector('.photo-preview'),status=root.querySelector('.photo-status'),upload=root.querySelector('[data-upload]'),remove=root.querySelector('[data-delete]'),refresh=root.querySelector('[data-refresh]');
    const clean=()=>{if(preview)URL.revokeObjectURL(preview);preview=null;selected=null;};this.cleanups.add(clean);
    const redraw=async()=>{display.textContent=initial(name);if(preview){const image=document.createElement('img');image.src=preview;image.alt='';display.replaceChildren(image);}else if(current.photoId){try{const url=await this.url(current);if(root.isConnected&&!preview){const image=document.createElement('img');image.src=url;image.alt='';display.replaceChildren(image);}}catch(error){status.textContent=error.message;}}};
    const controls=()=>{root.querySelectorAll('button,input').forEach(node=>node.disabled=busy);upload.disabled=busy||!selected||blocked;remove.disabled=busy||!current.photoId||blocked;const form=root.closest('form');if(form){if(busy)form.dataset.pending='1';else delete form.dataset.pending;}};
    const load=async()=>{busy=true;controls();try{current=await this.request(route(subject));this.metadata.set(subject,current);blocked=false;mutation=crypto.randomUUID();status.textContent='Referencia actualizada.';await redraw();}catch(error){blocked=true;status.textContent=error.message;}finally{busy=false;controls();}};
    input.addEventListener('change',()=>{clean();selected=input.files[0]??null;mutation=crypto.randomUUID();if(selected&&(selected.size>2097152||!['image/jpeg','image/png','image/webp'].includes(selected.type))){selected=null;status.textContent='Elige JPEG, PNG o WebP de hasta 2 MiB.';}else{if(selected)preview=URL.createObjectURL(selected);status.textContent=selected?'Previsualización local. Aún no se ha subido.':'';}redraw();controls();});
    const change=async deleting=>{busy=true;controls();status.textContent=deleting?'Eliminando foto compartida…':'Enviando imagen. Esperando confirmación del servidor…';const old=current.photoId;try{
      current=await this.request(route(subject),{method:deleting?'DELETE':'PUT',headers:{'If-Match':current.etag,...(!deleting?{'Content-Type':selected.type,'Idempotency-Key':mutation}:{})},...(!deleting?{body:selected}:{})});
      this.metadata.set(subject,current);if(old&&typeof this.urls.get(old)==='string'){URL.revokeObjectURL(this.urls.get(old));this.urls.delete(old);}clean();input.value='';status.textContent=deleting?'Foto compartida eliminada.':'Foto subida y confirmada.';await redraw();await this.hydrate(document);
    }catch(error){if(error.status===409)blocked=true;status.textContent=error.message;upload.textContent='Reintentar subida';}finally{busy=false;controls();}};
    upload.addEventListener('click',()=>change(false));remove.addEventListener('click',()=>change(true));refresh.addEventListener('click',load);controls();load();
  }
}
