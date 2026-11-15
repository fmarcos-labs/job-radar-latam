"""Salud de la corrida: lo que el correo tiene que decir cuando algo se rompió sin avisar.

Medido 15-11: Glassdoor llevaba 708 corridas sin aportar una fila y ningún correo lo decía; del 06 al 10-11
el Mac Mini quedó sin DNS, el radar remoto reventó con `KeyError: 'title'` y pasaron 4 días sin señal.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent / "job1"))
import helpers  # noqa: E402
import jobspy_search  # noqa: E402
from helpers import build_email_subject, export_results, send_alert_email  # noqa: E402
from salud import SaludCorrida, contar_por_fuente, evaluar_salud, ultima_corrida_con_datos  # noqa: E402

ESPERADAS = ["linkedin", "indeed", "glassdoor", "getonbrd"]
ESENCIALES = ["linkedin", "indeed", "getonbrd"]


def frame(site: str, filas: int) -> pd.DataFrame:
    return pd.DataFrame([{"site": site, "title": f"Dev {i}", "company": "Acme"} for i in range(filas)])


def run_con_total(job_dir: Path, run_id: str, total: int) -> None:
    run_dir = job_dir / run_id
    run_dir.mkdir()
    (run_dir / "results.csv").write_text(f"# CONFIG_VERSION=v10.5\n# TOTAL_RESULTADOS={total}\n#\n\"id\",\"site\"\n", encoding="utf-8")


def test_cuenta_filas_crudas_por_fuente_y_deja_en_cero_la_que_no_trajo_nada():
    conteo = contar_por_fuente([frame("linkedin", 3), frame("indeed", 2), frame("linkedin", 1)], ESPERADAS)
    assert conteo == {"linkedin": 4, "indeed": 2, "glassdoor": 0, "getonbrd": 0}


def test_frames_vacios_sin_columnas_cuentan_cero_y_no_revientan():
    # así vuelve JobSpy cuando la red no resuelve: DataFrames sin columna alguna
    conteo = contar_por_fuente([pd.DataFrame(), pd.DataFrame()], ESPERADAS)
    assert conteo == {"linkedin": 0, "indeed": 0, "glassdoor": 0, "getonbrd": 0}


def test_una_fuente_esencial_en_cero_es_aviso(tmp_path):
    salud = evaluar_salud([frame("linkedin", 5), frame("indeed", 2)], tmp_path, "20261115_1030", ESPERADAS, ESENCIALES)
    assert salud.avisos == ("fuente en 0: getonbrd",)
    assert not salud.sin_datos


def test_glassdoor_en_cero_no_avisa_porque_un_aviso_permanente_deja_de_leerse(tmp_path):
    frames = [frame("linkedin", 5), frame("indeed", 2), frame("getonbrd", 9)]
    salud = evaluar_salud(frames, tmp_path, "20261115_1030", ESPERADAS, ESENCIALES)
    assert salud.fuentes["glassdoor"] == 0
    assert salud.avisos == ()


def test_sin_ninguna_fila_la_corrida_queda_marcada_sin_datos(tmp_path):
    salud = evaluar_salud([pd.DataFrame()], tmp_path, "20261115_1030", ESPERADAS, ESENCIALES)
    assert salud.sin_datos
    assert salud.avisos == ("fuentes en 0: linkedin, indeed, getonbrd",)


def test_la_ultima_corrida_con_datos_salta_las_vacias_y_la_actual(tmp_path):
    run_con_total(tmp_path, "20261105_1730", 322)
    run_con_total(tmp_path, "20261107_1230", 0)       # el híbrido dejó carpetas con 0 filas durante la caída
    run_con_total(tmp_path, "20261110_1730", 292)     # la corrida en curso no cuenta como "anterior"
    (tmp_path / "__pycache__").mkdir()
    assert ultima_corrida_con_datos(tmp_path, antes_de="20261110_1730") == "20261105_1730"


def test_un_hueco_mayor_al_tope_entre_corridas_es_aviso(tmp_path):
    run_con_total(tmp_path, "20261105_1730", 322)
    frames = [frame("linkedin", 5), frame("indeed", 2), frame("getonbrd", 9)]
    salud = evaluar_salud(frames, tmp_path, "20261110_1730", ESPERADAS, ESENCIALES, max_horas=26)
    assert salud.avisos == ("sin corridas con datos desde 20261105_1730 (120 h)",)


def test_el_hueco_normal_entre_dos_corridas_del_dia_no_avisa(tmp_path):
    run_con_total(tmp_path, "20261114_1730", 307)
    frames = [frame("linkedin", 5), frame("indeed", 2), frame("getonbrd", 9)]
    salud = evaluar_salud(frames, tmp_path, "20261115_1030", ESPERADAS, ESENCIALES, max_horas=26)
    assert salud.avisos == ()


def test_la_primera_corrida_de_la_historia_no_avisa_hueco(tmp_path):
    frames = [frame("linkedin", 5), frame("indeed", 2), frame("getonbrd", 9)]
    assert evaluar_salud(frames, tmp_path, "20261115_1030", ESPERADAS, ESENCIALES).avisos == ()


SALUD_CON_AVISO = SaludCorrida(fuentes={"linkedin": 812, "indeed": 240, "glassdoor": 0, "getonbrd": 0}, avisos=("fuente en 0: getonbrd",))
SALUD_SANA = SaludCorrida(fuentes={"linkedin": 812, "indeed": 240, "glassdoor": 0, "getonbrd": 362}, avisos=())


def jobs() -> pd.DataFrame:
    return pd.DataFrame([
        {"site": "linkedin", "title": "Nuevo B", "company": "Kraken", "pais": "Chile", "date_posted": "2026-11-03", "job_url": "u2", "match_score": 4, "is_new": True},
    ])


def test_el_asunto_lleva_la_marca_de_aviso_solo_cuando_hay_avisos():
    con = build_email_subject(new_count=2, total=220, version="v10.6", sha="abc1234", run_id="20261115_1030", avisos=("fuente en 0: getonbrd",))
    sin = build_email_subject(new_count=2, total=220, version="v10.6", sha="abc1234", run_id="20261115_1030")
    assert con == f"⚠ {sin}"
    assert not sin.startswith("⚠")


def test_el_correo_html_muestra_las_filas_por_fuente_y_el_aviso_arriba(tmp_path):
    export_results(jobs(), [], tmp_path, "20261115_1030", version="v10.6", sha="abc1234", salud=SALUD_CON_AVISO)
    html = (tmp_path / "results.html").read_text(encoding="utf-8")
    assert "fuentes: linkedin 812 · indeed 240 · glassdoor 0 · getonbrd 0" in html
    assert html.index("⚠ fuente en 0: getonbrd") < html.index("NUEVOS (1)")


def test_el_results_md_tambien_lleva_fuentes_y_aviso(tmp_path):
    md = export_results(jobs(), [], tmp_path, "20261115_1030", version="v10.6", sha="abc1234", salud=SALUD_CON_AVISO).read_text(encoding="utf-8")
    assert "fuentes: linkedin 812 · indeed 240 · glassdoor 0 · getonbrd 0" in md
    assert "⚠ fuente en 0: getonbrd" in md


def test_una_corrida_sana_muestra_las_fuentes_sin_ninguna_marca_de_aviso(tmp_path):
    export_results(jobs(), [], tmp_path, "20261115_1030", version="v10.6", sha="abc1234", salud=SALUD_SANA)
    html = (tmp_path / "results.html").read_text(encoding="utf-8")
    assert "getonbrd 362" in html
    assert "⚠" not in html


def test_el_correo_de_alerta_dice_que_la_corrida_no_trajo_datos(monkeypatch):
    enviados = []
    monkeypatch.setenv("RESEND_API_KEY", "clave-de-prueba")
    monkeypatch.setenv("RESEND_TO_EMAIL", "yo@example.com")
    monkeypatch.setattr(helpers.resend.Emails, "send", lambda payload: enviados.append(payload))
    sin_datos = SaludCorrida(fuentes={"linkedin": 0, "indeed": 0, "glassdoor": 0, "getonbrd": 0}, avisos=("fuentes en 0: linkedin, indeed, getonbrd",))

    assert send_alert_email("20261107_1030", sin_datos, version="v10.6", sha="abc1234") is True

    assert len(enviados) == 1
    assert enviados[0]["subject"].startswith("⚠")
    assert "corrida sin datos" in enviados[0]["subject"]
    assert "20261107_1030" in enviados[0]["subject"]
    assert "fuentes en 0: linkedin, indeed, getonbrd" in enviados[0]["text"]


def test_un_scrape_vacio_termina_con_alerta_y_sin_reventar(monkeypatch, tmp_path):
    alertas = []
    monkeypatch.setattr(jobspy_search, "scrape_all_countries", lambda: [pd.DataFrame(), pd.DataFrame()])
    monkeypatch.setattr(jobspy_search, "scrape_getonbrd", lambda: pd.DataFrame())
    monkeypatch.setattr(jobspy_search, "JOB_DIR", tmp_path)
    monkeypatch.setattr(jobspy_search, "send_alert_email", lambda run_id, salud, **kw: alertas.append(salud) or True)

    jobspy_search.main()   # antes: KeyError 'title' en apply_filters

    assert len(alertas) == 1 and alertas[0].sin_datos
    assert [p.name for p in tmp_path.iterdir() if p.is_dir()] == []   # sin carpeta de corrida vacía


def aviso_indeed(n: int) -> dict:
    # pasa los dos radares: dice «remoto» (radar remoto) y «híbrido» (radar presencial/híbrido)
    return {
        "site": "indeed", "job_url": f"https://cl.indeed.com/viewjob?jk={n}", "title": f"Desarrollador React Node {n}",
        "company": "Acme", "location": "Santiago", "pais": "Chile", "date_posted": "2026-11-14",
        "description": "Trabajo híbrido o remoto. React, Node y TypeScript.",
    }


def test_una_corrida_normal_manda_el_correo_con_fuentes_y_marca_las_que_faltaron(monkeypatch, tmp_path):
    enviados = []
    monkeypatch.setenv("RESEND_API_KEY", "clave-de-prueba")
    monkeypatch.setenv("RESEND_TO_EMAIL", "yo@example.com")
    monkeypatch.delenv("RADAR_CLICK_BASE", raising=False)
    monkeypatch.setattr(helpers.resend.Emails, "send", lambda payload: enviados.append(payload))
    monkeypatch.setattr(jobspy_search, "scrape_all_countries", lambda: [pd.DataFrame([aviso_indeed(1), aviso_indeed(2)])])
    monkeypatch.setattr(jobspy_search, "scrape_getonbrd", lambda: pd.DataFrame())
    monkeypatch.setattr(jobspy_search, "JOB_DIR", tmp_path)
    monkeypatch.setattr(jobspy_search, "CLICKS_FILE", str(tmp_path / "clicks.json"))

    jobspy_search.main()

    assert len(enviados) == 1
    assert enviados[0]["subject"].startswith("⚠")                       # linkedin y getonbrd no trajeron nada
    assert "2 nuevos / 2" in enviados[0]["subject"]
    assert "⚠ fuentes en 0: linkedin, getonbrd" in enviados[0]["html"]
    assert "fuentes: linkedin 0 · indeed 2 · glassdoor 0 · getonbrd 0" in enviados[0]["html"]
    corridas = [p for p in tmp_path.iterdir() if p.is_dir()]
    assert len(corridas) == 1 and (corridas[0] / "results.csv").exists()
