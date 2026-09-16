from pathlib import Path


def test_lab_template_renders_theory_before_instructions():
    template = Path('templates/labs/detail_vm_exercise.html').read_text(encoding='utf-8')
    assert 'Before You Start' in template
    assert template.index('Before You Start') < template.index('Attack Instructions')
    assert 'pre_lab_theory_md' not in template or 'lab.pre_lab_theory_md' in template


def test_external_link_script_uses_pywebview_api():
    base_tpl = Path('templates/base_cybersec.html').read_text(encoding='utf-8')
    assert 'window.pywebview.api.open_external' in base_tpl
    assert 'data-external="true"' in base_tpl or 'data-external' in base_tpl
