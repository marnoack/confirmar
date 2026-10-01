"""
Visita la app de Streamlit con un navegador real (headless) para que la
conexión WebSocket se establezca de verdad y cuente como tráfico genuino.
Si la app está dormida, detecta el botón de "despertar" y hace clic en él.
"""
import os
import sys
from playwright.sync_api import sync_playwright

URL = os.environ["STREAMLIT_APP_URL"]


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        print(f"Visitando {URL} ...")
        page.goto(URL, wait_until="networkidle", timeout=60000)

        # Si la app está dormida, Streamlit Cloud muestra un botón para despertarla.
        boton_despertar = page.get_by_text("get this app back up", exact=False)
        try:
            if boton_despertar.is_visible(timeout=5000):
                print("La app estaba dormida. Haciendo clic para despertarla...")
                boton_despertar.click()
                # Espera a que el contenedor se reinicie y la app cargue de verdad.
                page.wait_for_timeout(15000)
                page.wait_for_load_state("networkidle", timeout=90000)
        except Exception:
            # No apareció el botón -> la app ya estaba despierta, todo bien.
            pass

        print("Título final de la página:", page.title())
        browser.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error al visitar la app: {e}")
        sys.exit(1)


