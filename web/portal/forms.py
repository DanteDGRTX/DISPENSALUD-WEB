from django import forms
from django.core.validators import RegexValidator


class RegistrationForm(forms.Form):
    display_name = forms.CharField(label="Tu nombre", max_length=120)
    username = forms.CharField(label="Nombre de usuario", min_length=4, max_length=40,
        validators=[RegexValidator(r"^[a-zA-Z0-9._-]+$", "Usa letras sin tildes, números, punto, guion o guion bajo.")])
    role = forms.ChoiceField(label="¿Cómo usarás DispenSalud?", choices=(("OLDER_ADULT", "Usuario"), ("CAREGIVER", "Cuidador")))
    password = forms.CharField(label="Contraseña", min_length=12, max_length=60, widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))
    password_confirmation = forms.CharField(label="Repite la contraseña", widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))
    accept = forms.BooleanField(label="Confirmo que esta cuenta es personal y que mantendré mi contraseña privada.")

    def clean_username(self):
        return self.cleaned_data["username"].lower()

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password") != cleaned.get("password_confirmation"):
            self.add_error("password_confirmation", "Las contraseñas no coinciden.")
        if len(cleaned.get("password", "").encode("utf-8")) > 72:
            self.add_error("password", "La contraseña excede el tamaño admitido. Usa menos caracteres.")
        return cleaned


class LoginForm(forms.Form):
    username = forms.CharField(label="Nombre de usuario", max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "username"}))
    password = forms.CharField(label="Contraseña", max_length=60,
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "current-password"}))


class MedicationForm(forms.Form):
    person_id = forms.UUIDField(widget=forms.HiddenInput)
    name = forms.CharField(label="Nombre del medicamento", max_length=120,
        widget=forms.TextInput(attrs={"class": "form-control"}))
    instructions = forms.CharField(label="Indicación registrada por el cuidador", max_length=500,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}))


class ScheduleForm(forms.Form):
    person_id = forms.UUIDField(widget=forms.HiddenInput)
    medication_id = forms.UUIDField(label="Identificador de medicamento", widget=forms.HiddenInput)
    local_time = forms.TimeField(label="Hora diaria (Perú)", input_formats=["%H:%M", "%H:%M:%S"],
        widget=forms.TimeInput(attrs={"type": "time", "class": "form-control"}, format="%H:%M"))
    start_date = forms.DateField(label="Desde", widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date", "class": "form-control"}))
    end_date = forms.DateField(label="Hasta (opcional)", required=False,
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date", "class": "form-control"}))


class IdentityForm(forms.Form):
    person_id = forms.UUIDField(widget=forms.HiddenInput)


class ScheduleToggleForm(IdentityForm):
    schedule_id = forms.UUIDField(widget=forms.HiddenInput)
    enabled = forms.TypedChoiceField(choices=(("true", "Activar"), ("false", "Pausar")), coerce=lambda value: value == "true")
