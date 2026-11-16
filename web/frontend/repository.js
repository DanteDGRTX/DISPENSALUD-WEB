import {collection,doc,getDocsFromServer,onSnapshot,runTransaction,serverTimestamp} from 'firebase/firestore';
import {KINDS,DomainError,ensure,validate,decode,editedTreatment,manualBody,planChanges,eventId} from './contract.js';

export class AccountRepository {
  constructor(db,uid,allowed=()=>true) {this.db=db;this.uid=uid;this.allowed=allowed;this.stops=[];this.active=true;}
  check() {if(!this.active || !this.allowed()) throw new DomainError('La sesión cambió. Vuelve a ingresar.','session-changed');}
  ref(kind,id) {ensure(KINDS.includes(kind),'Colección inválida.'); if(id) validateId(id); return id ? doc(this.db,'users',this.uid,kind,id) : collection(this.db,'users',this.uid,kind);}
  async unpack(kind,snap) {
    this.check(); const rows=snap.docs.map(d=>decode(kind,d.id,d.data(),this.uid));
    for(const d of rows) if(kind==='doseEvents' && d.body.origin==='GENERATED') ensure(d.id===await eventId(d.body.treatmentId,d.body.fechaHoraProgramada,d.body.planKey),'Identidad de dosis incompatible.');
    this.check(); return rows;
  }
  async load() {this.check(); const result=await Promise.all(KINDS.map(async k=>[k,await this.unpack(k,await getDocsFromServer(this.ref(k)))])); this.check(); return Object.fromEntries(result);}
  watch(changed,failed) {this.stops.forEach(stop=>stop());this.stops=[];for(const kind of KINDS) this.stops.push(onSnapshot(this.ref(kind),{includeMetadataChanges:true},snap=>{
    // Nunca presentar una caché local vacía como respuesta del servidor.
    if(snap.metadata.fromCache || snap.metadata.hasPendingWrites || !this.active) return;
    this.unpack(kind,snap).then(rows=>{if(this.active) changed(kind,rows);}).catch(e=>{if(this.active) failed(e);});
  },e=>{if(this.active) failed(e);}));}
  close(){this.active=false;this.stops.forEach(stop=>stop());this.stops=[];}
  envelope(kind,id,body,revision,deleted=false) {validate(kind,id,body);return {ownerUid:this.uid,id,schemaVersion:1,revision,mutationId:crypto.randomUUID(),deleted,updatedAt:serverTimestamp(),body};}
  expect(snap,expected) {
    if(expected ? !snap.exists() || snap.data().revision!==expected.revision || snap.data().mutationId!==expected.mutationId || snap.data().deleted : snap.exists()) throw new DomainError('Conflicto: otro dispositivo cambió este registro. Tu borrador sigue abierto; actualiza y vuelve a revisar antes de guardar.','conflict');
  }
  async save(kind,id,body,expected=null) {
    this.check(); validate(kind,id,body);
    await runTransaction(this.db,async tx=>{
      this.check(); const ref=this.ref(kind,id), snap=await tx.get(ref); this.expect(snap,expected);
      if(body.patientId){const parent=await tx.get(this.ref('patients',body.patientId));ensure(parent.exists() && !parent.data().deleted,'El paciente ya no está disponible.');}
      let next=body;
      if(kind==='treatments' && expected){ensure(body.patientId===snap.data().body.patientId,'No se puede cambiar el paciente.');next=editedTreatment(snap.data().body,body);}
      this.check();tx.set(ref,this.envelope(kind,id,next,(expected?.revision??0)+1));
    });this.check();
  }
  async reconcile(t,doses,now=Date.now()) {
    this.check(); const changes=await planChanges(t,doses,now);if(!changes.length) return 0;
    await runTransaction(this.db,async tx=>{
      this.check();const tr=await tx.get(this.ref('treatments',t.id));this.expect(tr,t);
      const patient=await tx.get(this.ref('patients',t.body.patientId));ensure(patient.exists() && !patient.data().deleted,'El paciente ya no está disponible.');
      // La revisión del tratamiento serializa las planificaciones web. Comprobar todas
      // las ocurrencias conocidas impide retirar un resultado manual recién confirmado.
      const known=doses.filter(d=>d.body.treatmentId===t.id), wanted=new Map(known.map(d=>[d.id,d]));
      changes.forEach(d=>{if(!wanted.has(d.id))wanted.set(d.id,null);});
      for(const [id,old] of wanted){const s=await tx.get(this.ref('doseEvents',id));if(old?.deleted){ensure(s.exists() && s.data().revision===old.revision,'Una baja cambió. Actualiza.');}else this.expect(s,old);}
      this.check();
      tx.set(this.ref('treatments',t.id),this.envelope('treatments',t.id,t.body,t.revision+1));
      for(const c of changes) tx.set(this.ref('doseEvents',c.id),this.envelope('doseEvents',c.id,c.body,c.revision+1,c.deleted));
    });this.check();return changes.length;
  }
  async recordManual(dose,treatment,allDoses,takenAt,omitted,now=Date.now()) {
    this.check(); const body=manualBody(dose,takenAt,omitted,now);
    await runTransaction(this.db,async tx=>{
      this.check();const ds=await tx.get(this.ref('doseEvents',dose.id));this.expect(ds,dose);
      const ts=await tx.get(this.ref('treatments',treatment.id));this.expect(ts,treatment);
      const ps=await tx.get(this.ref('patients',dose.body.patientId));ensure(ps.exists() && !ps.data().deleted,'El paciente ya no está disponible.');
      for(const other of allDoses.filter(d=>d.id!==dose.id && d.body.treatmentId===dose.body.treatmentId && d.body.fechaHoraProgramada===dose.body.fechaHoraProgramada)) {
        const s=await tx.get(this.ref('doseEvents',other.id));
        ensure(!s.exists() || s.data().deleted || s.data().body.estado==='PENDING','Ya existe un resultado para esta ocurrencia.');
      }
      this.check();tx.set(this.ref('treatments',treatment.id),this.envelope('treatments',treatment.id,ts.data().body,treatment.revision+1));
      tx.set(this.ref('doseEvents',dose.id),this.envelope('doseEvents',dose.id,body,dose.revision+1));
    });this.check();
  }
}
function validateId(id){ensure(typeof id==='string' && /^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/.test(id) && !/^demo-/i.test(id),'Identificador inválido.');}
