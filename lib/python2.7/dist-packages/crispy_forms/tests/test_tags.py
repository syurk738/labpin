# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from crispy_forms.exceptions import CrispyError
from crispy_forms.templatetags.crispy_forms_field import crispy_addon
from django.forms.forms import BoundField
from django.forms.models import formset_factory
from django.template import Context
import pytest

from .compatibility import get_template_from_string
from .conftest import only_bootstrap
from .forms import TestForm


def test_as_crispy_errors_form_without_non_field_errors():
    template = get_template_from_string("""
        {% load crispy_forms_tags %}
        {{ form|as_crispy_errors }}
    """)
    form = TestForm({'password1': "god", 'password2': "god"})
    form.is_valid()

    c = Context({'form': form})
    html = template.render(c)
    assert not ("errorMsg" in html or "alert" in html)


def test_as_crispy_errors_form_with_non_field_errors():
    template = get_template_from_string("""
        {% load crispy_forms_tags %}
        {{ form|as_crispy_errors }}
    """)
    form = TestForm({'password1': "god", 'password2': "wargame"})
    form.is_valid()

    c = Context({'form': form})
    html = template.render(c)
    assert "errorMsg" in html or "alert" in html
    assert "<li>Passwords dont match</li>" in html
    assert "<h3>" not in html


def test_as_crispy_errors_formset_without_non_form_errors():
    template = get_template_from_string("""
        {% load crispy_forms_tags %}
        {{ formset|as_crispy_errors }}
    """)

    TestFormset = formset_factory(TestForm, max_num=1, validate_max=True)
    formset = TestFormset()
    formset.is_valid()

    c = Context({'formset': formset})
    html = template.render(c)
    assert not ("errorMsg" in html or "alert" in html)


def test_as_crispy_errors_formset_with_non_form_errors():
    template = get_template_from_string("""
        {% load crispy_forms_tags %}
        {{ formset|as_crispy_errors }}
    """)

    TestFormset = formset_factory(TestForm, max_num=1, validate_max=True)
    formset = TestFormset({
        'form-TOTAL_FORMS': '2',
        'form-INITIAL_FORMS': '0',
        'form-MAX_NUM_FORMS': '',
        'form-0-password1': 'god',
        'form-0-password2': 'wargame',
    })
    formset.is_valid()

    c = Context({'formset': formset})
    html = template.render(c)
    assert "errorMsg" in html or "alert" in html
    assert "<li>Please submit 1 or fewer forms.</li>" in html
    assert "<h3>" not in html


def test_as_crispy_field_non_field(settings):
    template = get_template_from_string("""
        {% load crispy_forms_tags %}
        {{ field|as_crispy_field }}
    """)

    c = Context({'field': "notafield"})

    # Raises an AttributeError when tring to figure out how to render it
    # Not sure if this is exoected behavior -- @kavdev
    error_class = CrispyError if settings.DEBUG else AttributeError

    with pytest.raises(error_class):
        template.render(c)


def test_as_crispy_field_bound_field():
    template = get_template_from_string("""
        {% load crispy_forms_tags %}
        {{ field|as_crispy_field }}
    """)

    form = TestForm({'password1': "god", 'password2': "god"})
    form.is_valid()

    c = Context({'field': form["password1"]})

    # Would raise exception if not a field
    html = template.render(c)
    assert "id_password1" in html
    assert "id_password2" not in html


def test_crispy_filter_with_form():
    template = get_template_from_string("""
        {% load crispy_forms_tags %}
        {{ form|crispy }}
    """)
    c = Context({'form': TestForm()})
    html = template.render(c)

    assert "<td>" not in html
    assert "id_is_company" in html
    assert html.count('<label') == 7


def test_crispy_filter_with_formset():
    template = get_template_from_string("""
        {% load crispy_forms_tags %}
        {{ testFormset|crispy }}
    """)

    TestFormset = formset_factory(TestForm, extra=4)
    testFormset = TestFormset()

    c = Context({'testFormset': testFormset})
    html = template.render(c)

    assert html.count('<form') == 0
    # Check formset management form
    assert 'form-TOTAL_FORMS' in html
    assert 'form-INITIAL_FORMS' in html
    assert 'form-MAX_NUM_FORMS' in html


def test_classes_filter():
    template = get_template_from_string("""
        {% load crispy_forms_field %}
        {{ testField|classes }}
    """)

    test_form = TestForm()
    test_form.fields['email'].widget.attrs.update({'class': 'email-fields'})
    c = Context({'testField': test_form.fields['email']})
    html = template.render(c)
    assert 'email-fields' in html


def test_crispy_field_and_class_converters():
    template = get_template_from_string("""
        {% load crispy_forms_field %}
        {% crispy_field testField 'class' 'error' %}
    """)
    test_form = TestForm()
    field_instance = test_form.fields['email']
    bound_field = BoundField(test_form, field_instance, 'email')

    c = Context({'testField': bound_field})
    html = template.render(c)
    assert 'error' in html
    assert 'inputtext' in html


@only_bootstrap
def test_crispy_addon(settings):
    test_form = TestForm()
    field_instance = test_form.fields['email']
    bound_field = BoundField(test_form, field_instance, 'email')

    if settings.CRISPY_TEMPLATE_PACK == 'bootstrap':
        # prepend tests
        assert "input-prepend" in crispy_addon(bound_field, prepend="Work")
        assert "input-append" not in crispy_addon(bound_field, prepend="Work")
        # append tests
        assert "input-prepend" not in crispy_addon(bound_field, append="Primary")
        assert "input-append" in crispy_addon(bound_field, append="Secondary")
        # prepend and append tests
        assert "input-append" in crispy_addon(bound_field, prepend="Work", append="Primary")
        assert "input-prepend" in crispy_addon(bound_field, prepend="Work", append="Secondary")
    elif settings.CRISPY_TEMPLATE_PACK in ['bootstrap3', 'bootstrap4']:
        assert "input-group-addon" in crispy_addon(bound_field, prepend="Work", append="Primary")
        assert "input-group-addon" in crispy_addon(bound_field, prepend="Work", append="Secondary")

    # errors
    with pytest.raises(TypeError):
        crispy_addon()
    with pytest.raises(TypeError):
        crispy_addon(bound_field)
