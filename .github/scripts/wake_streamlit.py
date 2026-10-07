"""Abre la app en un navegador real para que Streamlit Cloud no la duerma.

Una simple petición (curl) no basta: Streamlit solo cuenta visitas que abren
la app en un navegador. Si ya está dormida, toca el botón para despertarla.
Si algo falla, imprime lo que se veía en la página para poder diagnosticarlo.
"""
import os
import re
import sys

from playwright.sync_api import sync_playwright

URL = os.environ.get("STREAMLIT_APP_URL", "").strip()
if not URL.startswith("http"):
    sys.exit("Falta el secreto STREAMLIT_APP_URL (ej. https://nuestraboda.streamlit.app).")

TEXTO_DE_LA_APP = "Nuestra boda"  # aparece en la pantalla de inicio de sesión


def app_cargada(pagina):
    """La app cargó si algún marco muestra la interfaz de Streamlit o el texto de la app."""
    for frame in pagina.frames:
        try:
            if (frame.locator('[data-testid="stAppViewContainer"]').count()
                    or frame.get_by_text(TEXTO_DE_LA_APP).count()):
                return True
        except Exception:
            pass  # un marco que se recarga mientras lo revisamos
    return False


def describir(pagina):
    """Qué había en la página, para entender un fallo desde el registro."""
    print("Dirección final:", pagina.url)
    print("Título:", pagina.title())
    for frame in pagina.frames:
        try:
            texto = " ".join(frame.locator("body").inner_text(timeout=3000).split())
        except Exception:
            texto = "(no se pudo leer)"
        print(f"- Marco {frame.url[:80]}: {texto[:300] or '(vacío)'}")


with sync_playwright() as p:
    navegador = p.chromium.launch()
    pagina = navegador.new_page()
    print(f"Visitando {URL}")
    pagina.goto(URL, wait_until="domcontentloaded", timeout=90_000)
    pagina.wait_for_timeout(10_000)

    boton = pagina.get_by_role("button", name=re.compile("get this app back up", re.I))
    if boton.count():
        print("La app estaba dormida: despertándola…")
        boton.first.click()
        espera_maxima = 240  # segundos: al despertar puede tardar
    else:
        print("La app estaba despierta.")
        espera_maxima = 120

    for _ in range(espera_maxima // 5):
        if app_cargada(pagina):
            print("La app cargó correctamente.")
            pagina.wait_for_timeout(15_000)  # se queda un momento, como una visita real
            navegador.close()
            sys.exit(0)
        pagina.wait_for_timeout(5_000)

    pagina.screenshot(path="error.png", full_page=True)
    print("La app no terminó de cargar. Esto es lo que se veía:")
    describir(pagina)
    navegador.close()
    sys.exit(1)
