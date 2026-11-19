package pe.dispensalud.portal.adapters;

import java.net.URI;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.*;
import pe.dispensalud.core.*;
import pe.dispensalud.core.CareData.*;

@Component
public class SupervisionHttpAdapter implements SupervisionPort {
    private final RestClient client; private final String url, token;
    public SupervisionHttpAdapter(RestClient client, @Value("${dispensalud.supervision.url}") String url,
            @Value("${dispensalud.supervision.token}") String token) {
        URI uri = URI.create(url);
        boolean loopback = "http".equals(uri.getScheme()) && "127.0.0.1".equals(uri.getHost());
        if ((!loopback && !"https".equals(uri.getScheme())) || uri.getUserInfo()!=null ||
            uri.getQuery()!=null || uri.getFragment()!=null || !uri.getPath().isEmpty() || token.length()<32)
            throw new IllegalArgumentException("Configura una dirección de supervisión y una clave de al menos 32 caracteres.");
        this.client=client; this.url=url; this.token=token;
    }
    @Override public Report inspect(Inspection inspection) {
        try {
            Report report=client.post().uri(url+"/inspect").headers(h -> h.setBearerAuth(token))
                .body(inspection).retrieve().body(Report.class);
            if (report==null || !"COMPLETED".equals(report.state())) throw new IllegalStateException();
            return report;
        } catch (Exception error) {
            throw new CareFailure(CareFailure.Kind.UNAVAILABLE,"La supervisión no está disponible. Tus pacientes siguen guardados.");
        }
    }
}
