from django import forms
from django.contrib.auth.forms import AuthenticationForm


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label  # placeholderにフィールドのラベルを入れる


class ASForm(forms.Form):
    name = forms.CharField(
        label="name",
        required=False,
    )

    ipv6 = forms.BooleanField(label="ipv6", required=False)

    collection_interval = forms.IntegerField(
        label="収集頻度(分)",
        required=True,
    )

    asn = forms.IntegerField(
        label="ASN",
        required=True,
    )

    p12 = forms.FileField(label="ファイル(.p12)", required=False)

    p12_pass = forms.CharField(
        label="p12パスワード",
        required=False,
    )


class ChangeCertForm(forms.Form):
    p12 = forms.FileField(label="ファイル(.p12)", required=False)

    p12_pass = forms.CharField(
        label="p12パスワード",
        required=False,
    )
