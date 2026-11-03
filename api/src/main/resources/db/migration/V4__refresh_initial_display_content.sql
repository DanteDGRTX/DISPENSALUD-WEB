UPDATE accounts SET display_name = 'Elena'
WHERE username = 'usuario.demo' AND display_name = 'Elena (persona ficticia)';

UPDATE accounts SET display_name = 'Cuidadora'
WHERE username = 'cuidador.demo' AND display_name = 'Cuidadora de prueba';

UPDATE medications
SET name = CASE WHEN name IN ('Ejemplo ficticio A', 'Ejemplo ficticio B')
    THEN REPLACE(name, 'Ejemplo ficticio ', 'Medicamento ') ELSE 'Medicamento adicional' END,
    instructions = 'Consulta las indicaciones registradas por tu cuidador.'
WHERE person_id IN (SELECT id FROM accounts WHERE username = 'usuario.demo')
AND name LIKE 'Ejemplo ficticio %'
AND instructions IN (
    'Demostracion de pantalla. No corresponde a un tratamiento real.',
    'Registro ficticio de verificación. No es una indicación médica.',
    'Texto de demostración para revisar cómo se muestran tus indicaciones. Este registro no corresponde a un tratamiento real.'
);
