from ingesta.carga_bronze import main

USO = "uso: python -m ingesta.carga_bronze trm [--completo] | ipc [ruta.csv] | tasa [ruta.csv] | usura | brent | fed | cdt\n"


def test_argumentos_invalidos_muestran_el_uso(capsys):
    assert main(["otra"]) == 2
    salida = capsys.readouterr()
    assert (salida.out, salida.err) == ("", USO)


def test_sin_argumentos_muestra_el_uso(capsys):  # comportamiento previo de trm
    assert main([]) == 2
    assert capsys.readouterr().err == USO


def test_csv_inexistente_termina_con_error_sin_crear_lote(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr("ingesta.carga_bronze.RAIZ_LAKE", tmp_path)
    ruta = tmp_path / "no-existe.csv"
    assert main(["ipc", str(ruta)]) == 1
    salida = capsys.readouterr()
    assert (salida.out, salida.err) == ("", f"error: no existe el archivo {ruta}\n")
    assert list(tmp_path.iterdir()) == []  # no se escribió ningún lote


def test_trm_que_no_se_puede_extraer_termina_con_error_sin_crear_lote(tmp_path, capsys, monkeypatch):  # HU-06
    from ingesta.extractores.trm_socrata import ExtraccionError

    def falla(**_):
        raise ExtraccionError("no se pudo extraer la TRM tras 4 intentos: sin red")

    monkeypatch.setattr("ingesta.carga_bronze.RAIZ_LAKE", tmp_path)
    monkeypatch.setattr("ingesta.carga_bronze.desde_trm", lambda completo: "2020-01-01")
    monkeypatch.setattr("ingesta.extractores.trm_socrata.extraer_trm", falla)
    assert main(["trm"]) == 1
    salida = capsys.readouterr()
    assert (salida.out, salida.err) == ("", "error: no se pudo extraer la TRM tras 4 intentos: sin red\n")
    assert list(tmp_path.iterdir()) == []


def _trm_con_captura(monkeypatch, tmp_path, desde):
    """Corre `trm` sin red ni base; devuelve el `desde` con el que se pidió la fuente."""
    pedidos = []
    monkeypatch.setattr("ingesta.carga_bronze.RAIZ_LAKE", tmp_path)
    monkeypatch.setattr("ingesta.carga_bronze.desde_trm", lambda completo: "2020-01-01" if completo else desde)
    monkeypatch.setattr("ingesta.extractores.trm_socrata.extraer_trm", lambda **kw: pedidos.append(kw["desde"]) or [])
    monkeypatch.setattr("ingesta.carga_bronze.conectar", lambda: _FalsaConexion())
    monkeypatch.setattr("ingesta.carga_bronze.crear_tablas", lambda c: None)
    monkeypatch.setattr("ingesta.carga_bronze.cargar_trm", lambda *a, **k: None)
    return pedidos


class _FalsaConexion:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_trm_pide_a_la_fuente_desde_la_ultima_vigencia_cargada(tmp_path, monkeypatch):
    pedidos = _trm_con_captura(monkeypatch, tmp_path, "2026-10-16")
    assert main(["trm"]) == 0
    assert pedidos == ["2026-10-16"]


def test_trm_completo_ignora_lo_cargado_y_pide_todo(tmp_path, monkeypatch):
    pedidos = _trm_con_captura(monkeypatch, tmp_path, "2026-10-16")
    assert main(["trm", "--completo"]) == 0
    assert pedidos == ["2020-01-01"]


def test_fuentes_api_conocidas_se_cargan_con_extractor_y_nombre_de_fuente(tmp_path, monkeypatch, capsys):
    from ingesta import carga_bronze

    cargadas = []
    monkeypatch.setattr(carga_bronze, "RAIZ_LAKE", tmp_path)
    monkeypatch.setattr(carga_bronze, "conectar", lambda: _FalsaConexion())
    monkeypatch.setattr(carga_bronze, "crear_tablas", lambda c: None)
    monkeypatch.setattr(carga_bronze, "cargar_api", lambda c, nombre, filas, fuente, lote, ahora: cargadas.append((nombre, filas, fuente)))
    monkeypatch.setitem(carga_bronze.FUENTES_API, "fed", ("fred/FEDFUNDS", lambda conn: [{"x": "1"}]))
    assert main(["fed"]) == 0
    assert cargadas == [("fed", [{"x": "1"}], "fred/FEDFUNDS")]
    assert "fed: 1 registros" in capsys.readouterr().out


def test_fuente_api_que_falla_termina_con_error_sin_crear_lote(tmp_path, monkeypatch, capsys):
    from ingesta import carga_bronze
    from ingesta.extractores.fred import ExtraccionError

    def falla(conn):
        raise ExtraccionError("sin red")

    monkeypatch.setattr(carga_bronze, "RAIZ_LAKE", tmp_path)
    monkeypatch.setattr(carga_bronze, "conectar", lambda: _FalsaConexion())
    monkeypatch.setattr(carga_bronze, "crear_tablas", lambda c: None)
    monkeypatch.setitem(carga_bronze.FUENTES_API, "fed", ("fred/FEDFUNDS", falla))
    assert main(["fed"]) == 1
    assert capsys.readouterr().err == "error: sin red\n"
    assert list(tmp_path.iterdir()) == []


def test_cdt_pide_solo_el_plazo_a_90_dias_desde_la_ultima_fecha_cargada(monkeypatch):
    import datetime as dt

    from ingesta import carga_bronze
    from ingesta.extractores import trm_socrata

    pedidos = []
    monkeypatch.setattr(trm_socrata, "extraer_socrata", lambda url, where, order, **kw: pedidos.append((url, where, order)) or [])
    monkeypatch.setattr(carga_bronze, "ultima_fecha_cdt", lambda conn: dt.date(2026, 11, 3))
    assert carga_bronze.FUENTES_API["cdt"][1](None) == []
    url, where, order = pedidos[0]
    assert url.endswith("/axk9-g2nh.json")
    assert "descripcion = 'A 90 DIAS'" in where and "fechacorte >= '2026-10-27T00:00:00'" in where
    assert "fechacorte" in order
