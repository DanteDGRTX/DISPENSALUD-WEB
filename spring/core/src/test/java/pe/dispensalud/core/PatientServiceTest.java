package pe.dispensalud.core;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import pe.dispensalud.core.CareData.*;
import java.util.*;

class PatientServiceTest {
    static class Memory implements CareRepository {
        PatientRecord row; boolean hasHistory; int writes;
        public Snapshot snapshot(String uid) {
            return new Snapshot(row==null?List.of():List.of(row), List.of(),
                hasHistory?List.of(new Dose("d","p","t",1,"PENDING")):List.of());
        }
        public PatientRecord findPatient(String uid,String id){return row;}
        public void writePatient(String uid,String id,Patient body,PatientRecord expected,boolean deleted){
            writes++; row=new PatientRecord(id,body,new Version(expected==null?1:expected.version().revision()+1,"next"),"server-time",deleted);
        }
    }
    Patient sample(){return new Patient("FICTICIO",60,"","Contacto ficticio");}
    @Test void staleEditsCannotOverwriteConfirmedChanges(){
        Memory db=new Memory();db.row=new PatientRecord("p",sample(),new Version(2,"new"),"time",false);
        assertThrows(CareFailure.class,()->new PatientService(db).save("a","p",sample(),new Version(1,"old")));
        assertEquals(0,db.writes);
    }
    @Test void historyPreventsRemoval(){
        Memory db=new Memory();db.row=new PatientRecord("p",sample(),new Version(1,"v"),"time",false);db.hasHistory=true;
        assertThrows(CareFailure.class,()->new PatientService(db).remove("a","p",new Version(1,"v")));
        assertEquals(0,db.writes);
    }
    @Test void removalIsATombstoneAndBumpsVersion(){
        Memory db=new Memory();db.row=new PatientRecord("p",sample(),new Version(1,"v"),"time",false);
        new PatientService(db).remove("a","p",new Version(1,"v"));
        assertTrue(db.row.deleted());assertEquals(2,db.row.version().revision());assertEquals(sample(),db.row.body());
    }
    @Test void invalidPatientNeverReachesPersistence(){
        assertThrows(IllegalArgumentException.class,()->new Patient(" ",131,"",""));
    }
}
