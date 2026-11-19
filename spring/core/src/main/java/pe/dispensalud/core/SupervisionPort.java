package pe.dispensalud.core;

import pe.dispensalud.core.CareData.*;

public interface SupervisionPort {
    Report inspect(Inspection inspection);
}
