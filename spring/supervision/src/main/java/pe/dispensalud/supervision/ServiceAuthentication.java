package pe.dispensalud.supervision;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import jakarta.servlet.*;
import jakarta.servlet.http.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

@Component
public class ServiceAuthentication extends OncePerRequestFilter {
    private final byte[] expected;
    public ServiceAuthentication(@Value("${dispensalud.supervision.token}") String token) {
        if (token.length()<32) throw new IllegalArgumentException("Configura una clave interna de al menos 32 caracteres.");
        expected=("Bearer "+token).getBytes(StandardCharsets.UTF_8);
    }
    @Override protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
            throws ServletException, IOException {
        response.setHeader("Cache-Control","no-store");
        response.setHeader("X-Content-Type-Options","nosniff");
        if (request.getRequestURI().equals("/health")) { chain.doFilter(request,response); return; }
        String authorization=request.getHeader("Authorization");
        if (authorization==null || authorization.length()>512 ||
                !MessageDigest.isEqual(expected,authorization.getBytes(StandardCharsets.UTF_8))) {
            response.setStatus(401); response.setContentType("application/json");
            response.getWriter().write("{\"error\":\"Servicio no autorizado.\"}"); return;
        }
        chain.doFilter(request,response);
    }
}
