// Contrato v1 de SyncCodec / Models / DosePlanner Android. Sin datos de demostración.
export const KINDS = ['patients', 'treatments', 'doseEvents', 'alerts', 'preferences'];
export class DomainError extends Error { constructor(message, code = 'invalid-data') { super(message); this.code = code; } }
export const ensure = (ok, message) => { if (!ok) throw new DomainError(message); };
export const validId = id => typeof id === 'string' && /^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/.test(id) && !/^demo-/i.test(id);
const integer = (v, min, max) => Number.isSafeInteger(v) && v >= min && v <= max;
const text = (v, n) => typeof v === 'string' && v.trim().length > 0 && v.length <= n;
const instant = v => integer(v, -62135596800000, 253402300799999);
const day = v => integer(v, -719162, 2932896);
const keys = (b, required, optional = []) => required.every(k => Object.hasOwn(b, k)) && Object.keys(b).every(k => [...required, ...optional].includes(k));
export function validate(kind, id, b) {
  ensure(KINDS.includes(kind) && validId(id) && b && typeof b === 'object', 'Registro inválido.');
  if (kind === 'patients') ensure(keys(b, ['nombre','edad','foto','notas','contactoEmergencia']) && text(b.nombre,120) && integer(b.edad,0,130) && b.foto === null && typeof b.notas === 'string' && b.notas.length <= 4000 && text(b.contactoEmergencia,200), 'Revisa nombre, edad, notas y contacto de emergencia.');
  if (kind === 'treatments') ensure(keys(b, ['patientId','medicamento','dosis','horarios','compartimento','fechaInicio','fechaFin','activo'], ['scheduleRevision']) && validId(b.patientId) && text(b.medicamento,200) && text(b.dosis,200) && Array.isArray(b.horarios) && b.horarios.length >= 1 && b.horarios.length <= 24 && new Set(b.horarios).size === b.horarios.length && b.horarios.every(h => typeof h === 'string' && /^([01]\d|2[0-3]):[0-5]\d$/.test(h)) && integer(b.compartimento,1,28) && day(b.fechaInicio) && (b.fechaFin === null || day(b.fechaFin) && b.fechaFin >= b.fechaInicio) && typeof b.activo === 'boolean' && integer(b.scheduleRevision ?? 0,0,999999999), 'Revisa medicamento, dosis, horarios únicos HH:mm, compartimento (1–28) y fechas.');
  if (kind === 'doseEvents') {
    const meta = ['origin','planKey','recordSource','recordedAt'];
    const any = meta.some(k => Object.hasOwn(b,k));
    ensure(keys(b, ['patientId','treatmentId','fechaHoraProgramada','fechaHoraReal','estado'], [...meta,'retiredByPlanKey']) && validId(b.patientId) && validId(b.treatmentId) && instant(b.fechaHoraProgramada) && ['PENDING','TAKEN','LATE','MISSED'].includes(b.estado) && (['TAKEN','LATE'].includes(b.estado) ? instant(b.fechaHoraReal) : b.fechaHoraReal === null) && (b.estado !== 'LATE' || b.fechaHoraReal > b.fechaHoraProgramada), 'Dosis incompatible.');
    if (any) ensure(meta.every(k => Object.hasOwn(b,k)) && ['LEGACY','GENERATED','MANUAL'].includes(b.origin) && (b.origin === 'GENERATED' ? /^[a-f0-9]{64}$/.test(b.planKey) : b.planKey === '') && (b.recordSource === null && b.recordedAt === null || b.recordSource === 'MANUAL' && instant(b.recordedAt) && b.fechaHoraProgramada <= b.recordedAt && b.estado !== 'PENDING' && (b.fechaHoraReal === null || b.fechaHoraReal <= b.recordedAt) && (b.estado !== 'TAKEN' || b.fechaHoraReal <= b.fechaHoraProgramada)), 'Procedencia de dosis incompatible.');
    if (Object.hasOwn(b,'retiredByPlanKey')) ensure(b.origin === 'GENERATED' && b.estado === 'PENDING' && /^[a-f0-9]{64}$/.test(b.retiredByPlanKey), 'Baja de dosis incompatible.');
  }
  if (kind === 'alerts') ensure(keys(b, ['patientId','tipo','mensaje','fecha','leida']) && validId(b.patientId) && ['DOSIS_OMITIDA','STOCK_BAJO','BATERIA_BAJA','DESCONECTADO'].includes(b.tipo) && text(b.mensaje,2000) && instant(b.fecha) && typeof b.leida === 'boolean', 'Alerta incompatible.');
  if (kind === 'preferences') ensure(id === 'presentation' && keys(b, ['profile']) && ['Usuario','Cuidador'].includes(b.profile), 'Selecciona Usuario o Cuidador.');
  return b;
}
export function decode(kind, id, d, uid) {
  ensure(keys(d,['ownerUid','id','schemaVersion','revision','mutationId','deleted','updatedAt','body']) && d.ownerUid === uid && d.id === id && d.schemaVersion === 1 && integer(d.revision,1,999999999) && /^[A-Za-z0-9-]{1,128}$/.test(d.mutationId) && typeof d.deleted === 'boolean' && d.updatedAt && typeof d.updatedAt.toMillis === 'function', 'Datos remotos incompatibles. Actualiza la página o revisa la versión Android.');
  validate(kind,id,d.body);
  return { ...d, kind };
}
export function epochDay(iso) {
  ensure(/^\d{4}-\d{2}-\d{2}$/.test(iso), 'Fecha inválida.');
  const v = Date.parse(iso + 'T00:00:00Z') / 86400000;
  ensure(day(v) && dateInput(v) === iso, 'Fecha inválida.');
  return v;
}
export const dateInput = days => new Date(days * 86400000).toISOString().slice(0,10);
export const limaDay = millis => Math.floor((millis - 5 * 3600000) / 86400000);
export function limaInstant(iso, time) { epochDay(iso); ensure(/^([01]\d|2[0-3]):[0-5]\d$/.test(time), 'Hora inválida.'); return Date.parse(`${iso}T${time}:00-05:00`); }
export const formatInstant = millis => new Intl.DateTimeFormat('es-PE', {timeZone:'America/Lima', dateStyle:'medium', timeStyle:'short'}).format(millis);
export const timeInput = millis => new Intl.DateTimeFormat('en-GB',{timeZone:'America/Lima',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).format(millis);
export const sha256 = async text => Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text))), b=>b.toString(16).padStart(2,'0')).join('');
export const planKey = t => sha256(['v1',t.id,t.body.patientId,t.body.scheduleRevision ?? 0,t.body.fechaInicio,t.body.fechaFin ?? '',t.body.activo,[...t.body.horarios].sort().join(',')].join('|'));
export const eventId = async (id, at, key) => 'dose-' + await sha256(`v1|${id}|${at}|${key}`);
export const sameSchedule = (a,b) => a.patientId === b.patientId && [...a.horarios].sort().join() === [...b.horarios].sort().join() && a.fechaInicio === b.fechaInicio && a.fechaFin === b.fechaFin && a.activo === b.activo;
export function editedTreatment(old, body) { return {...body, scheduleRevision:(old.scheduleRevision ?? 0) + (sameSchedule(old,body) ? 0 : 1)}; }
export function manualBody(old, takenAt, omitted, now) {
  ensure(!old.deleted && old.body.estado === 'PENDING', 'Esta dosis cambió o ya tiene un resultado. Actualiza antes de registrar.');
  const b = old.body;
  ensure(b.fechaHoraProgramada <= now && (omitted ? takenAt === null : instant(takenAt) && takenAt <= now), 'No puedes confirmar una dosis ni una hora real futuras.');
  return validate('doseEvents', old.id, {...b, origin:b.origin ?? 'LEGACY',planKey:b.planKey ?? '',fechaHoraReal:takenAt,estado:omitted ? 'MISSED' : takenAt > b.fechaHoraProgramada ? 'LATE' : 'TAKEN',recordSource:'MANUAL',recordedAt:now});
}
// Equivalente a DosePlanner: horizonte [ahora, ahora+7d), conserva resultados y horarios vigentes.
export async function planChanges(t, doses, now) {
  if (t.deleted) return [];
  const b=t.body, key=await planKey(t), end=now+7*86400000, rows=doses.filter(d=>d.body.treatmentId===t.id), changes=[];
  const retired = new Set(rows.filter(d=>d.deleted).map(d=>d.id));
  const inSchedule = d => b.activo && b.horarios.includes(timeInput(d.body.fechaHoraProgramada)) && limaDay(d.body.fechaHoraProgramada) >= b.fechaInicio && (b.fechaFin===null || limaDay(d.body.fechaHoraProgramada)<=b.fechaFin) && d.body.fechaHoraProgramada % 60000 === 0;
  const retire = d => { changes.push({...d,deleted:true,body:{...d.body,retiredByPlanKey:key}}); retired.add(d.id); };
  for (const d of rows) if (!retired.has(d.id) && d.body.origin==='GENERATED' && d.body.estado==='PENDING' && d.body.fechaHoraProgramada>=now && !inSchedule(d)) retire(d);
  if (!b.activo) return changes;
  const groups = new Map();
  for (const d of rows) if (!retired.has(d.id) && d.body.fechaHoraProgramada>=now) { const at=d.body.fechaHoraProgramada; groups.set(at,[...(groups.get(at)??[]),d]); }
  for (const group of groups.values()) {
    const pending=group.filter(d=>d.body.origin==='GENERATED' && d.body.estado==='PENDING').sort((a,b)=>a.id < b.id ? -1 : a.id > b.id ? 1 : 0);
    const losers=group.some(d=>d.body.origin!=='GENERATED' || d.body.estado!=='PENDING') ? pending : pending.slice(1);
    losers.forEach(retire);
  }
  for (let date=Math.max(b.fechaInicio,limaDay(now)); date<=Math.min(b.fechaFin??limaDay(end),limaDay(end)); date++) for (const time of [...b.horarios].sort()) {
    const at=limaInstant(dateInput(date),time); if (at<now || at>=end) continue;
    const id=await eventId(t.id,at,key);
    if(rows.some(d=>d.id===id)) continue;
    if(rows.some(d=>{const retiredBody=changes.find(c=>c.id===d.id)?.body??d.body;return d.body.fechaHoraProgramada===at && retired.has(d.id) && (retiredBody.origin!=='GENERATED' || retiredBody.retiredByPlanKey==null || retiredBody.retiredByPlanKey===key);})) continue;
    if(rows.some(d=>d.body.fechaHoraProgramada===at && !retired.has(d.id))) continue;
    changes.push({id,kind:'doseEvents',deleted:false,revision:0,body:{patientId:b.patientId,treatmentId:t.id,fechaHoraProgramada:at,fechaHoraReal:null,estado:'PENDING',origin:'GENERATED',planKey:key,recordSource:null,recordedAt:null}});
  }
  return changes;
}
export function metrics(doses, now) {
  const due=doses.filter(d=>!d.deleted && d.body.fechaHoraProgramada<=now);
  const taken=due.filter(d=>['TAKEN','LATE'].includes(d.body.estado)).length;
  return {due:due.length,taken,percent:due.length ? Math.round(100*taken/due.length):null,overdue:due.filter(d=>d.body.estado==='PENDING').length,missed:due.filter(d=>d.body.estado==='MISSED').length};
}
export function readableError(e) {
  if (e instanceof DomainError) return e.message;
  const code=(e?.code??'').replace('auth/','').replace('firestore/','');
  return ({'permission-denied':'Firebase rechazó los permisos. Comprueba el correo verificado y la compatibilidad de las reglas publicadas con Android. No se han sustituido tus datos por una lista vacía.',unavailable:'No hay conexión con Firebase. Reintenta cuando tengas Internet.','network-request-failed':'No se pudo conectar. Revisa tu conexión a Internet.','invalid-credential':'Correo o contraseña incorrectos.','wrong-password':'Correo o contraseña incorrectos.','user-not-found':'Correo o contraseña incorrectos.','invalid-email':'Escribe un correo electrónico válido.','email-already-in-use':'Ese correo ya está registrado. Inicia sesión o recupera tu contraseña.','weak-password':'Usa una contraseña de al menos 6 caracteres.','too-many-requests':'Demasiados intentos. Espera unos minutos antes de reintentar.','user-disabled':'Esta cuenta está deshabilitada.','requires-recent-login':'Vuelve a iniciar sesión para continuar.','resource-exhausted':'Se alcanzó la cuota de Firebase. Espera antes de reintentar.',aborted:'Otro dispositivo cambió los datos. Actualiza y revisa tu edición.',unauthenticated:'La sesión venció. Vuelve a ingresar.'})[code] ?? 'No se pudo completar la operación. Reintenta; si continúa, revisa la configuración de Firebase.';
}
