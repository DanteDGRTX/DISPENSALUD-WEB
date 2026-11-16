// Web presentation only. Firebase services and event identifiers live in main.js.
export const assets = '/static/portal/firebase/assets/';
export const product = '/static/portal/product/images/';
export const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const image = (name, className = '') => `<img class="${className}" src="${assets}${name}" alt="" aria-hidden="true">`;
const paths = {
  home: '<path d="m3 10 9-7 9 7v10H3Z"/><path d="M9 20v-7h6v7"/>',
  person: '<circle cx="12" cy="8" r="4"/><path d="M4 21v-2a8 8 0 0 1 16 0v2"/>',
  pill: '<path d="m9 5 10 10M5 9l4-4a7 7 0 0 1 10 10l-4 4A7 7 0 0 1 5 9Z"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  activity: '<path d="M4 4v16h16M7 14l4-5 4 3 5-7"/>',
  alert: '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"/>',
  device: '<rect x="5" y="3" width="14" height="18" rx="4"/><path d="M9 7h6m-6 5h6m-4 5h2"/>',
};
export const svg = name => `<svg class="icon" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name] ?? paths.person}</svg>`;
export const navigationIcon = {panel:'home',patients:'person',treatments:'pill',history:'activity',alerts:'alert',device:'device',profile:'person'};

export function roleChoices(current) {
  return `<fieldset class="role-choices"><legend>Tu perfil</legend><div class="role-cards">${['Usuario','Cuidador'].map(role => `<label class="role-card"><input type="radio" name="profile" value="${role}" ${current === role ? 'checked' : ''} required>${image(role === 'Usuario' ? 'profile_user.svg' : 'profile_caregiver.svg','profile-illustration')}<strong>${role}</strong><small>${role === 'Usuario' ? 'Consultar y organizar tus horarios.' : 'Organizar y acompañar.'}</small></label>`).join('')}</div></fieldset>`;
}

export function accountView({mode,email,title,banner,form}) {
  const login = mode === 'login';
  return `<section class="integration-section account-section"><div class="container account-layout"><div class="account-intro"><p class="eyebrow-blue">${login ? 'TU ESPACIO DE CUIDADO' : 'UN ACCESO PARA CADA PERSONA'}</p><h1>${login ? 'Bienvenido<br>a DispenSalud.' : mode === 'register' ? 'Tu cuenta.<br>Tu forma de cuidar.' : mode === 'reset' ? 'Volver a tu<br>espacio de cuidado.' : 'Un paso más<br>para cuidar.'}</h1><p>${login ? 'La presentación del proyecto y tu espacio personal están separados. Ingresa para consultar tu horario o acompañar a la persona que cuidas.' : mode === 'register' ? 'Elige si usarás DispenSalud para consultar tus horarios o para acompañar como cuidador.' : 'Conserva tu cuenta personal y continúa organizando tus horarios desde la web.'}</p>
  ${login ? `<div class="role-cards"><a href="?perfil=usuario" class="role-card" data-profile="Usuario">${image('profile_user.svg','profile-illustration')}<strong>Usuario</strong><small>Consultar tus horarios.</small></a><a href="?perfil=cuidador" class="role-card" data-profile="Cuidador">${image('profile_caregiver.svg','profile-illustration')}<strong>Cuidador</strong><small>Organizar y acompañar.</small></a></div><p class="section-caption">El perfil no concede acceso a datos de otras cuentas.</p>` : `<div class="account-rule"><strong>La privacidad empieza con tu cuenta.</strong><p>Los perfiles Usuario y Cuidador conservan sus propios datos. La colaboración entre cuentas no está disponible.</p></div>`}
  <figure class="account-product"><img src="${product}pillbox-transparent.png" width="629" height="397" alt="Dispensador Dispensalud PillBox Pro"><figcaption>Diseño del producto · La imagen no indica una conexión física.</figcaption></figure></div>
  <section class="account-card" aria-labelledby="login-title"><span class="eyebrow-blue">${mode === 'register' ? 'NUEVA CUENTA' : 'MI CUENTA'}</span><h2 id="login-title">${escapeHtml(title)}</h2><p>${mode === 'verify' ? escapeHtml(email) : mode === 'reset' ? 'Te enviaremos un enlace para restablecer tu contraseña.' : 'Ingresa con tus credenciales personales.'}</p>${banner}${form}</section></div></section>`;
}

export function workspaceView({page,labels,urls,profile,banner,sync,selector,content}) {
  const links = Object.entries(labels).map(([key,label]) => `<a href="${urls[key]}" data-nav="${key}" ${page === key ? 'aria-current="page"' : ''}>${svg(navigationIcon[key])}<span>${label}</span></a>`).join('');
  return `<div class="web-workspace care-app"><div class="app-frame"><aside class="sidebar"><p class="sidebar-label">ACOMPAÑAR Y CUIDAR</p><nav class="desktop-nav" aria-label="Mi cuenta">${links}</nav><div class="sidebar-note">${svg('device')}<strong>Tu dispensador</strong><p>Sin dispositivo vinculado</p><span>Por ahora puedes organizar y consultar tus horarios.</span></div></aside><div class="app-content"><div class="panel-context"><span class="account-role">${image(profile === 'Cuidador' ? 'profile_caregiver.svg' : 'profile_user.svg','profile-small')}${profile}</span><div class="web-account-actions"><button class="panel-refresh" data-action="refresh">${svg('clock')} Actualizar</button><button class="font-button" data-action="font" aria-label="Aumentar el tamaño del texto">A+</button><button class="btn btn-quiet" data-action="logout">Salir</button></div></div><details class="workspace-menu"><summary>Secciones de mi cuenta</summary><nav class="desktop-nav" aria-label="Mi cuenta móvil">${links}</nav></details><div class="sync-line">${sync}</div>${banner}<div class="surface person-picker">${selector}</div>${content}</div></div><footer class="container footer-note">DispenSalud · Tus horarios, siempre claros. <span>Hora de Perú · Registro manual; no acredita ingestión.</span></footer></div>`;
}
