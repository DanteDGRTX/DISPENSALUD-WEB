package pe.dispensalud.portal.adapters;

import com.fasterxml.jackson.databind.JsonNode;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.stereotype.Repository;
import org.springframework.web.client.*;
import pe.dispensalud.core.*;
import pe.dispensalud.core.CareData.*;
import static pe.dispensalud.core.CareFailure.Kind.*;

@Repository
public class FirestoreRepository implements CareRepository {
    private final RestClient client;
    private final String root;
    public FirestoreRepository(RestClient client, @Value("${dispensalud.firebase.project}") String project) {
        if (!project.matches("[a-z0-9-]{3,80}")) throw new IllegalArgumentException("Proyecto inválido.");
        this.client = client;
        root = "projects/" + project + "/databases/(default)/documents";
    }
    private String token(String uid) {
        Object principal = SecurityContextHolder.getContext().getAuthentication().getPrincipal();
        if (!(principal instanceof Jwt jwt) || !uid.equals(jwt.getSubject()))
            throw new CareFailure(FORBIDDEN, "Cuenta no autorizada.");
        if (!uid.matches("[A-Za-z0-9][A-Za-z0-9_-]{0,127}")) throw new CareFailure(FORBIDDEN, "Cuenta no autorizada.");
        return jwt.getTokenValue();
    }
    private JsonNode get(String uid, String path) {
        try {
            return client.get().uri("https://firestore.googleapis.com/v1/" + root + "/users/" + uid + "/" + path)
                .headers(h -> h.setBearerAuth(token(uid))).retrieve().body(JsonNode.class);
        } catch (HttpClientErrorException.NotFound missing) { return null; }
        catch (RestClientException error) { throw unavailable(); }
    }
    private List<JsonNode> list(String uid, String kind) {
        List<JsonNode> rows = new ArrayList<>(); String page = "";
        do {
            JsonNode response = get(uid, kind + "?pageSize=200" +
                (page.isEmpty() ? "" : "&pageToken=" + URLEncoder.encode(page, StandardCharsets.UTF_8)));
            if (response == null) throw unavailable();
            for (JsonNode doc : response.path("documents")) {
                if (rows.size() >= 5000) throw new CareFailure(LIMIT, "La cuenta supera el límite de esta vista. Usa los filtros de la aplicación.");
                envelope(doc, uid); rows.add(doc);
            }
            page = response.path("nextPageToken").asText("");
        } while (!page.isEmpty());
        return rows;
    }
    private JsonNode envelope(JsonNode doc, String uid) {
        JsonNode fields = doc.path("fields");
        String id = text(fields, "id");
        if (!uid.equals(text(fields,"ownerUid")) || !doc.path("name").asText().endsWith("/" + id) ||
            number(fields,"schemaVersion") != 1 || number(fields,"revision") < 1 ||
            !fields.path("deleted").path("booleanValue").isBoolean() ||
            !fields.path("body").path("mapValue").path("fields").isObject())
            throw unavailable();
        return fields;
    }
    private PatientRecord patient(JsonNode doc, String uid) {
        JsonNode fields = envelope(doc, uid), body = fields.path("body").path("mapValue").path("fields");
        Set<String> keys = new HashSet<>(); body.fieldNames().forEachRemaining(keys::add);
        if (!keys.equals(Set.of("nombre","edad","foto","notas","contactoEmergencia")) ||
            !body.path("foto").has("nullValue")) throw unavailable();
        return new PatientRecord(text(fields,"id"),
            new Patient(text(body,"nombre"), Math.toIntExact(number(body,"edad")), text(body,"notas"), text(body,"contactoEmergencia")),
            new Version(number(fields,"revision"), text(fields,"mutationId")), doc.path("updateTime").asText(),
            fields.path("deleted").path("booleanValue").booleanValue());
    }
    @Override public PatientRecord findPatient(String uid, String id) {
        if (!id.matches("[A-Za-z0-9][A-Za-z0-9_-]{0,127}")) throw new CareFailure(NOT_FOUND, "Paciente no disponible.");
        JsonNode doc = get(uid, "patients/" + id); return doc == null ? null : patient(doc, uid);
    }
    @Override public Snapshot snapshot(String uid) {
        List<PatientRecord> patients = list(uid,"patients").stream().map(d -> patient(d, uid)).filter(d -> !d.deleted()).toList();
        List<Treatment> treatments = new ArrayList<>();
        for (JsonNode doc : list(uid,"treatments")) {
            JsonNode f=doc.path("fields"), b=f.path("body").path("mapValue").path("fields");
            if (!f.path("deleted").path("booleanValue").booleanValue())
                treatments.add(new Treatment(text(f,"id"),text(b,"patientId"), b.path("activo").path("booleanValue").booleanValue()));
        }
        List<Dose> doses = new ArrayList<>();
        for (JsonNode doc : list(uid,"doseEvents")) {
            JsonNode f=doc.path("fields"), b=f.path("body").path("mapValue").path("fields");
            if (!f.path("deleted").path("booleanValue").booleanValue()) {
                String state = text(b,"estado");
                if (!Set.of("PENDING","TAKEN","LATE","MISSED").contains(state)) throw unavailable();
                doses.add(new Dose(text(f,"id"),text(b,"patientId"),text(b,"treatmentId"),number(b,"fechaHoraProgramada"),state));
            }
        }
        // Keep references even when a parent was removed: deletion must not orphan history.
        return new Snapshot(patients, treatments, doses);
    }
    @Override public void writePatient(String uid, String id, Patient body, PatientRecord expected, boolean deleted) {
        String auth = token(uid);
        long revision = expected == null ? 1 : expected.version().revision() + 1;
        if (revision > 999999999) throw new CareFailure(LIMIT, "Se alcanzó el límite de revisiones.");
        Map<String,Object> patient = new LinkedHashMap<>();
        patient.put("nombre", string(body.nombre())); patient.put("edad", integer(body.edad()));
        patient.put("foto", Collections.singletonMap("nullValue", null)); patient.put("notas", string(body.notas()));
        patient.put("contactoEmergencia", string(body.contactoEmergencia()));
        Map<String,Object> fields = new LinkedHashMap<>();
        fields.put("ownerUid",string(uid)); fields.put("id",string(id)); fields.put("schemaVersion",integer(1));
        fields.put("revision",integer(revision)); fields.put("mutationId",string(UUID.randomUUID().toString()));
        fields.put("deleted", Map.of("booleanValue",deleted)); fields.put("body", Map.of("mapValue",Map.of("fields",patient)));
        Map<String,Object> precondition = expected == null ? Map.of("exists",false) : Map.of("updateTime",expected.updateTime());
        Map<String,Object> write = Map.of("update",Map.of("name",root+"/users/"+uid+"/patients/"+id,"fields",fields),
            "updateTransforms",List.of(Map.of("fieldPath","updatedAt","setToServerValue","REQUEST_TIME")),
            "currentDocument",precondition);
        try {
            client.post().uri("https://firestore.googleapis.com/v1/"+root+":commit")
                .headers(h -> h.setBearerAuth(auth)).body(Map.of("writes",List.of(write))).retrieve().toBodilessEntity();
        } catch (HttpClientErrorException error) {
            if (error.getStatusCode().value()==409 || error.getStatusCode().value()==412 ||
                error.getResponseBodyAsString().contains("FAILED_PRECONDITION"))
                throw new CareFailure(CONFLICT,"Otro dispositivo cambió el paciente. Actualiza y revisa tu edición.");
            throw unavailable();
        } catch (RestClientException error) { throw unavailable(); }
    }
    static Map<String,Object> string(String value) { return Map.of("stringValue",value); }
    static Map<String,Object> integer(long value) { return Map.of("integerValue",Long.toString(value)); }
    static String text(JsonNode fields, String name) {
        JsonNode node = fields.path(name).path("stringValue");
        if (!node.isTextual()) throw unavailable(); return node.textValue();
    }
    static long number(JsonNode fields, String name) {
        try {
            JsonNode node=fields.path(name).path("integerValue");
            if (!node.isTextual() && !node.isIntegralNumber()) throw unavailable();
            return Long.parseLong(node.asText());
        } catch (NumberFormatException error) { throw unavailable(); }
    }
    static CareFailure unavailable() { return new CareFailure(UNAVAILABLE,"No se pudieron confirmar los datos con Firebase. Reintenta."); }
}
